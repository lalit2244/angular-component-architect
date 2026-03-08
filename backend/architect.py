"""
Guided Component Architect - Main Orchestrator
Agentic pipeline: Generate → Validate → Self-Correct → Output
"""

import json
import re
import os
import sys
from pathlib import Path
from groq import Groq

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
MAX_RETRIES = 2
MODEL = "llama-3.3-70b-versatile"


def load_design_tokens() -> dict:
    possible_paths = [
        Path(__file__).parent.parent / "design-system" / "tokens.json",
        Path(__file__).parent / "tokens.json",
        Path("design-system") / "tokens.json",
        Path("../design-system") / "tokens.json",
    ]
    for p in possible_paths:
        if p.exists():
            with open(p) as f:
                return json.load(f)
    raise FileNotFoundError("tokens.json not found in any expected location")


def build_system_prompt(tokens: dict) -> str:
    token_str = json.dumps(tokens, indent=2)
    return f"""You are an expert Angular/TypeScript developer and UI designer.
Your job is to generate COMPLETE, VALID Angular components using inline styles.

=== DESIGN SYSTEM (STRICT - YOU MUST USE THESE TOKENS) ===
{token_str}

=== RULES ===
1. Output ONLY raw code — no markdown fences, no explanations, no comments outside code.
2. Generate a SINGLE self-contained Angular component as a TypeScript file.
3. Use ONLY colors from the design system (primary: #6366f1, secondary: #06b6d4, etc.).
4. Use ONLY border-radius values from the design system (4px, 8px, 12px, 16px, 24px, 9999px).
5. Always explicitly set font-family: 'Inter', sans-serif on the component root element.
6. All brackets/braces/parentheses must be properly closed.
7. Component selector must be kebab-case (e.g., app-login-card).
8. Include @Component decorator with selector, template, and styles.
9. Use inline template strings (no separate HTML file reference).
10. The component must be visually polished and match the user description exactly.
11. ALL cards and containers MUST have: box-sizing: border-box; min-width: 0; overflow: hidden; word-break: break-word;
12. Text inside cards must NEVER overflow — always use word-wrap: break-word; overflow-wrap: break-word;
13. For row layouts ALWAYS use: display: flex; flex-wrap: wrap; gap: 16px; width: 100%; box-sizing: border-box;
14. Each card in a row MUST have: flex: 1 1 140px; min-width: 140px; max-width: 100%; box-sizing: border-box;
15. Numbers and metric values MUST use: font-size that fits — never overflow the card width.
16. The root host element style MUST include: display: block; width: 100%; box-sizing: border-box;
17. Never use fixed pixel widths on cards — use flex or percentage widths only.
18. Padding inside cards should be at least 12px on all sides.

=== OUTPUT FORMAT ===
Start directly with: import {{ Component }} from '@angular/core';
End with the exported class. Nothing else.
"""


def generate_component(client: Groq, system_prompt: str, user_prompt: str, feedback: str = "") -> str:
    messages = [{"role": "user", "content": user_prompt}]
    if feedback:
        messages = [
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": "// previous attempt had errors"},
            {
                "role": "user",
                "content": f"Fix these validation errors and regenerate the COMPLETE component:\n\n{feedback}",
            },
        ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system_prompt}, *messages],
        temperature=0.3,
        max_tokens=4096,
    )
    return response.choices[0].message.content.strip()


# ─────────────────────────────────────────────
# VALIDATOR / LINTER AGENT
# ─────────────────────────────────────────────

class ValidationError:
    def __init__(self, rule: str, message: str, severity: str = "error"):
        self.rule = rule
        self.message = message
        self.severity = severity

    def __str__(self):
        return f"[{self.severity.upper()}] {self.rule}: {self.message}"


def validate_component(code: str, tokens: dict) -> list[ValidationError]:
    errors = []

    # 1. Check Angular structure
    if "@Component" not in code:
        errors.append(ValidationError("ANGULAR_STRUCTURE", "Missing @Component decorator"))
    if "selector:" not in code:
        errors.append(ValidationError("ANGULAR_STRUCTURE", "Missing selector in @Component"))
    if "template:" not in code and "templateUrl:" not in code:
        errors.append(ValidationError("ANGULAR_STRUCTURE", "Missing template in @Component"))
    if not re.search(r"export\s+class\s+\w+", code):
        errors.append(ValidationError("ANGULAR_STRUCTURE", "Missing exported class"))

    # 2. Bracket balance check
    errors.extend(_check_bracket_balance(code))

    # 3. Design token compliance — colors
    errors.extend(_check_color_compliance(code, tokens))

    # 4. Design token compliance — border-radius
    errors.extend(_check_border_radius_compliance(code, tokens))

    # 5. Font compliance
    errors.extend(_check_font_compliance(code, tokens))

    # 6. Check for forbidden conversational filler
    if code.strip().startswith("```") or "```" in code[:50]:
        errors.append(ValidationError("OUTPUT_FORMAT", "Code wrapped in markdown fences — output raw code only"))

    return errors


def _check_bracket_balance(code: str) -> list[ValidationError]:
    errors = []
    stack = []
    pairs = {")": "(", "}": "{", "]": "["}
    opens = set("({[")
    closes = set(")}]")

    in_string = False
    string_char = None
    i = 0
    while i < len(code):
        ch = code[i]
        if in_string:
            if ch == "\\" and i + 1 < len(code):
                i += 2
                continue
            if ch == string_char:
                in_string = False
        else:
            if ch in ('"', "'", "`"):
                in_string = True
                string_char = ch
            elif ch in opens:
                stack.append(ch)
            elif ch in closes:
                if not stack or stack[-1] != pairs[ch]:
                    errors.append(ValidationError("SYNTAX", f"Unmatched closing bracket '{ch}' at position {i}"))
                    return errors
                stack.pop()
        i += 1

    if stack:
        errors.append(ValidationError("SYNTAX", f"Unclosed brackets: {stack}"))
    return errors


def _check_color_compliance(code: str, tokens: dict) -> list[ValidationError]:
    errors = []
    allowed_colors = set(tokens.get("colors", {}).values())

    hex_colors = re.findall(r"#([0-9a-fA-F]{3,8})\b", code)
    for hex_val in hex_colors:
        full = f"#{hex_val}"
        if len(hex_val) == 3:
            full = "#" + "".join(c * 2 for c in hex_val)
        if full.lower() not in [c.lower() for c in allowed_colors]:
            errors.append(
                ValidationError(
                    "DESIGN_TOKEN_COLOR",
                    f"Color '{full}' is NOT in the design system. Allowed: {sorted(allowed_colors)}",
                    severity="error",
                )
            )
    return errors


def _check_border_radius_compliance(code: str, tokens: dict) -> list[ValidationError]:
    errors = []
    allowed_radii = set(tokens.get("borders", {}).values())
    radius_matches = re.findall(r"border-?[Rr]adius[:\s]+([^;\"'`}]+)", code)
    for match in radius_matches:
        for val in match.strip().split():
            val = val.rstrip(";,\"'")
            if re.match(r"^\d+px$", val) and val not in allowed_radii:
                errors.append(
                    ValidationError(
                        "DESIGN_TOKEN_RADIUS",
                        f"border-radius '{val}' not in design system. Allowed px values: {sorted(v for v in allowed_radii if 'px' in str(v))}",
                        severity="warning",
                    )
                )
    return errors


def _check_font_compliance(code: str, tokens: dict) -> list[ValidationError]:
    errors = []
    allowed_fonts = [
        tokens["typography"]["font-family-sans"],
        tokens["typography"]["font-family-mono"],
        "Inter",
        "JetBrains Mono",
        "sans-serif",
        "monospace",
        "serif",
        "inherit",
        "initial",
        "unset",
    ]
    font_matches = re.findall(r"font-family[:\s]+([^;\"'`}]+)", code)
    for match in font_matches:
        match_clean = match.strip().strip("'\"").strip()
        if not match_clean:
            continue
        if any(af.lower() in match.lower() for af in allowed_fonts):
            continue
        errors.append(
            ValidationError(
                "DESIGN_TOKEN_FONT",
                f"Font '{match_clean}' not in design system. Use 'Inter' or 'JetBrains Mono'",
                severity="warning",
            )
        )
    return errors


# ─────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────

def run_pipeline(user_prompt: str, api_key: str, conversation_history: list = None) -> dict:
    """
    Agentic loop:
    1. Generate component
    2. Validate (lint)
    3. If errors → self-correct with feedback → repeat up to MAX_RETRIES
    4. Return final result
    """
    client = Groq(api_key=api_key)
    tokens = load_design_tokens()
    system_prompt = build_system_prompt(tokens)

    # Build prompt with conversation history for multi-turn
    full_prompt = user_prompt
    if conversation_history:
        history_str = "\n".join(
            [f"[Previous turn - {h['role']}]: {h['content'][:200]}..." for h in conversation_history[-4:]]
        )
        full_prompt = f"Previous conversation context:\n{history_str}\n\nNew request: {user_prompt}"

    print(f"\n{'='*60}")
    print(f"Generating component for: {user_prompt}")
    print(f"{'='*60}")

    code = ""
    all_errors = []
    attempt = 0
    feedback = ""

    for attempt in range(MAX_RETRIES + 1):
        print(f"\n{'─'*40}")
        print(f"Attempt {attempt + 1}/{MAX_RETRIES + 1}: Calling LLM...")
        code = generate_component(client, system_prompt, full_prompt, feedback)

        print(f"Generated {len(code)} characters of code")
        print(f"\nRunning Linter-Agent...")

        errors = validate_component(code, tokens)
        hard_errors = [e for e in errors if e.severity == "error"]
        warnings    = [e for e in errors if e.severity == "warning"]
        all_errors  = errors

        if warnings:
            print(f"{len(warnings)} warning(s):")
            for w in warnings:
                print(f"   {w}")

        if not hard_errors:
            print(f"Validation PASSED! ({len(warnings)} warnings)")
            break
        else:
            print(f"Validation FAILED — {len(hard_errors)} error(s):")
            for e in hard_errors:
                print(f"   {e}")

            if attempt < MAX_RETRIES:
                print(f"\nSelf-correcting... (retry {attempt + 1}/{MAX_RETRIES})")
                feedback = "VALIDATION ERRORS FROM LINTER:\n" + "\n".join(str(e) for e in hard_errors)
                feedback += "\n\nFix ALL errors above. Output ONLY the corrected raw TypeScript code."
            else:
                print(f"\nMax retries reached. Returning best attempt.")

    return {
        "code":        code,
        "errors":      [str(e) for e in all_errors],
        "warnings":    [str(e) for e in all_errors if e.severity == "warning"],
        "hard_errors": [str(e) for e in all_errors if e.severity == "error"],
        "attempts":    attempt + 1,
        "success":     len([e for e in all_errors if e.severity == "error"]) == 0,
        "prompt":      user_prompt,
    }


if __name__ == "__main__":
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        print("Set GROQ_API_KEY environment variable")
        sys.exit(1)

    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "A login card with glassmorphism effect"
    result = run_pipeline(prompt, api_key)

    print(f"\n{'='*60}")
    print("FINAL RESULT")
    print(f"{'='*60}")
    print(f"Success:  {result['success']}")
    print(f"Attempts: {result['attempts']}")
    print(f"\n--- COMPONENT CODE ---\n")
    print(result["code"])
