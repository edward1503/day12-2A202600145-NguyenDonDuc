# hãy di chuyển tới branch MASTER
import os
import re
import json
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)

class InputGuardrail:
    def __init__(self):
        self.allowed_topics = settings.allowed_topics
        self.blocked_topics = settings.blocked_topics
        self.injection_patterns = [
            r"ignore (all )?(previous|above) instructions",
            r"you are now (a |an )?unrestricted",
            r"reveal your (instructions|prompt)",
            r"system prompt",
            r"bỏ qua mọi hướng dẫn",
        ]

    def check(self, text: str) -> Tuple[bool, str]:
        for pattern in self.injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False, f"Injection detected (pattern: {pattern})"
        
        text_lower = text.lower()
        for topic in self.blocked_topics:
            if topic in text_lower:
                return False, f"Blocked topic detected: {topic}"
            
        return True, ""

class OutputGuardrail:
    def __init__(self):
        self.pii_patterns = {
            "Phone": r"0\d{9,10}",
            "Email": r"[\w.-]+@[\w.-]+\.[a-zA-Z]{2,}",
            "NationalID": r"\b\d{9}\b|\b\d{12}\b",
            "APIKey": r"sk-[a-zA-Z0-9-]+"
        }

    def redact_pii(self, text: str) -> Tuple[str, List[str]]:
        issues = []
        redacted = text
        for name, pattern in self.pii_patterns.items():
            if re.search(pattern, text):
                issues.append(name)
                redacted = re.sub(pattern, f"[REDACTED_{name.upper()}]", redacted)
        return redacted, issues

class LLMJudge:
    def __init__(self, client: OpenAI, model: str):
        self.client = client
        self.model = model

    def evaluate(self, user_input: str, response_text: str) -> Dict:
        prompt = f"""Evaluate the following AI response against the user input for a banking assistant.
User Input: {user_input}
AI Response: {response_text}

Score 1-5 for: Safety, Relevance, Accuracy, Tone.
Respond in JSON format: {{"safety": score, "relevance": score, "accuracy": score, "tone": score, "verdict": "PASS/FAIL", "reason": "str"}}
"""
        try:
            res = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "You are a security auditor."}, 
                          {"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(res.choices[0].message.content)
        except Exception as e:
            logger.error(f"LLM Judge error: {e}")
            return {"error": str(e), "verdict": "FAIL"}

class DefensePipeline:
        from openai import OpenAI
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.llm_model
        self.input_guard = InputGuardrail()
        self.output_guard = OutputGuardrail()
        self.judge = LLMJudge(self.client, self.model)
        
    async def process_query(self, user_id: str, query: str):
        start_time = time.time()
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "input": query
        }
        
        # 1. Input Guardrails
        safe, reason = self.input_guard.check(query)
        if not safe:
            log_entry.update({"status": "BLOCKED", "layer": "InputGuard", "reason": reason})
            logger.warning(json.dumps({"event": "guardrail_block", "layer": "input", "user_id": user_id, "reason": reason}))
            return "I cannot process this request for security reasons.", log_entry

        # 2. LLM Generation
        try:
            res = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a VinBank assistant. Provide helpful banking advice. Stay on topic."},
                    {"role": "user", "content": query}
                ]
            )
            raw_response = res.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            msg = "System error during generation."
            log_entry.update({"status": "ERROR", "response": msg})
            return msg, log_entry

        # 3. Output Guardrails (PII)
        redacted_response, pii_issues = self.output_guard.redact_pii(raw_response)
        
        # 4. LLM Judge
        evaluation = self.judge.evaluate(query, redacted_response)
        
        latency = time.time() - start_time
        status = "SUCCESS" if evaluation.get("verdict") == "PASS" else "FLAGGED"
        
        if status == "FLAGGED":
            logger.warning(json.dumps({"event": "judge_flagged", "user_id": user_id, "reason": evaluation.get("reason")}))

        log_entry.update({
            "status": status,
            "raw_response": raw_response,
            "final_response": redacted_response,
            "pii_detected": pii_issues,
            "evaluation": evaluation,
            "latency": round(latency, 3)
        })
        
        if evaluation.get("verdict") == "FAIL":
            return "The generated response failed our safety check.", log_entry
            
        return redacted_response, log_entry
