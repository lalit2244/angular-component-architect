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
    raise FileNotFoundError("tokens.json not found")


def build_system_prompt(tokens: dict) -> str:
    token_str = json.dumps(tokens, indent=2)
    return f"""You are an expert Angular/TypeScript developer and UI designer.
Generate COMPLETE, VALID, VISUALLY IMPRESSIVE Angular components using inline styles.

=== DESIGN SYSTEM (YOU MUST USE THESE TOKENS ONLY) ===
{token_str}

=== STRICT RULES ===
1. Output ONLY raw TypeScript code — NO markdown fences, NO backtick code blocks, NO explanations.
2. Single self-contained Angular component TypeScript file only.
3. Use ONLY hex colors from the design system above. NO other hex colors allowed.
4. Use ONLY border-radius values: 4px, 8px, 12px, 16px, 24px, or 9999px.
5. Font must always be: font-family: 'Inter', sans-serif on the root host element.
6. All brackets/braces/parentheses must be properly closed and balanced.
7. Component selector must be kebab-case (e.g., app-login-card).
8. Use @Component decorator with selector, template, and styles array.
9. Use backtick template strings for template and styles.

=== LAYOUT & OVERFLOW RULES (CRITICAL) ===
10. Root host style MUST be: display: block; width: 100%; box-sizing: border-box;
11. All cards MUST have: box-sizing: border-box; min-width: 0; padding: 16px;
12. Row of cards MUST use: display: flex; flex-wrap: wrap; gap: 16px; width: 100%;
13. Each card in a row: flex: 1 1 150px; min-width: 150px; max-width: 100%;
14. NEVER use fixed pixel widths like width: 300px — use flex or percentages only.
15. All text must wrap: word-break: break-word; overflow-wrap: break-word;

=== VISUAL QUALITY RULES ===
16. ALWAYS use unicode emoji or SVG icons for visual elements — e.g. 👤 📊 💰 ⏱ ✓ ★
17. For glassmorphism: background: rgba(255,255,255,0.08); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.18);
18. For profile avatars: use a div with initials (e.g. "JD") styled as a circle — NEVER use <img> tags.
19. Add hover effects using CSS transitions for buttons: transition: all 0.2s ease;
20. Primary buttons must use: background: #6366f1; color: #ffffff; border: none; cursor: pointer;
21. Input fields must show placeholder text and have visible labels above them.
22. Dashboard metric cards MUST show: colored icon area at top, large bold number, small label below.
23. Metric card icon area: background: rgba(99,102,241,0.15); border-radius: 8px; padding: 8px; display: inline-flex;
24. Use proper visual hierarchy — titles large and bold, subtitles medium, body text small.
25. Cards must have visible shadows: box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1);

=== OUTPUT FORMAT ===
Start EXACTLY with: import {{ Component }} from '@angular/core';
End with the closing brace of the exported class. NOTHING else before or after.
"""


def generate_component(client: Groq, system_prompt: str, user_prompt: str, feedback: str = "") -> str:
    messages = [{"role": "user", "content": user_prompt}]
    if feedback:
        messages = [
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": "// previous attempt had errors"},
            {
                "role": "user",
                "content": f"Fix ALL these validation errors and regenerate the COMPLETE component:\n\n{feedback}\n\nOutput ONLY raw TypeScript. No markdown.",
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

    if "@Component" not in code:
        errors.append(ValidationError("ANGULAR_STRUCTURE", "Missing @Component decorator"))
    if "selector:" not in code:
        errors.append(ValidationError("ANGULAR_STRUCTURE", "Missing selector in @Component"))
    if "template:" not in code and "templateUrl:" not in code:
        errors.append(ValidationError("ANGULAR_STRUCTURE", "Missing template in @Component"))
    if not re.search(r"export\s+class\s+\w+", code):
        errors.append(ValidationError("ANGULAR_STRUCTURE", "Missing exported class"))

    errors.extend(_check_bracket_balance(code))
    errors.extend(_check_color_compliance(code, tokens))
    errors.extend(_check_border_radius_compliance(code, tokens))
    errors.extend(_check_font_compliance(code, tokens))

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
            errors.append(ValidationError(
                "DESIGN_TOKEN_COLOR",
                f"Color '{full}' NOT in design system. Allowed: {sorted(allowed_colors)}",
                severity="error",
            ))
    return errors


def _check_border_radius_compliance(code: str, tokens: dict) -> list[ValidationError]:
    errors = []
    allowed_radii = set(tokens.get("borders", {}).values())
    radius_matches = re.findall(r"border-?[Rr]adius[:\s]+([^;\"'`}]+)", code)
    for match in radius_matches:
        for val in match.strip().split():
            val = val.rstrip(";,\"'")
            if re.match(r"^\d+px$", val) and val not in allowed_radii:
                errors.append(ValidationError(
                    "DESIGN_TOKEN_RADIUS",
                    f"border-radius '{val}' not in design system. Allowed: {sorted(v for v in allowed_radii if 'px' in str(v))}",
                    severity="warning",
                ))
    return errors


def _check_font_compliance(code: str, tokens: dict) -> list[ValidationError]:
    errors = []
    allowed_fonts = [
        tokens["typography"]["font-family-sans"],
        tokens["typography"]["font-family-mono"],
        "Inter", "JetBrains Mono", "sans-serif", "monospace", "serif",
        "inherit", "initial", "unset",
    ]
    font_matches = re.findall(r"font-family[:\s]+([^;\"'`}]+)", code)
    for match in font_matches:
        match_clean = match.strip().strip("'\"").strip()
        if not match_clean:
            continue
        if any(af.lower() in match.lower() for af in allowed_fonts):
            continue
        errors.append(ValidationError(
            "DESIGN_TOKEN_FONT",
            f"Font '{match_clean}' not in design system. Use 'Inter' or 'JetBrains Mono'",
            severity="warning",
        ))
    return errors


# ─────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────

def run_pipeline(user_prompt: str, api_key: str, conversation_history: list = None) -> dict:
    client = Groq(api_key=api_key)
    tokens = load_design_tokens()
    system_prompt = build_system_prompt(tokens)

    full_prompt = user_prompt
    if conversation_history:
        history_str = "\n".join(
            [f"[Previous - {h['role']}]: {h['content'][:200]}..." for h in conversation_history[-4:]]
        )
        full_prompt = f"Previous context:\n{history_str}\n\nNew request: {user_prompt}"

    print(f"\n{'='*60}")
    print(f"Generating: {user_prompt}")
    print(f"{'='*60}")

    code = ""
    all_errors = []
    attempt = 0
    feedback = ""

    for attempt in range(MAX_RETRIES + 1):
        print(f"\nAttempt {attempt + 1}/{MAX_RETRIES + 1}")
        code = generate_component(client, system_prompt, full_prompt, feedback)
        print(f"Generated {len(code)} chars")

        errors = validate_component(code, tokens)
        hard_errors = [e for e in errors if e.severity == "error"]
        warnings    = [e for e in errors if e.severity == "warning"]
        all_errors  = errors

        if warnings:
            print(f"{len(warnings)} warning(s): {[str(w) for w in warnings]}")

        if not hard_errors:
            print(f"PASSED ({len(warnings)} warnings)")
            break
        else:
            print(f"FAILED {len(hard_errors)} errors: {[str(e) for e in hard_errors]}")
            if attempt < MAX_RETRIES:
                feedback = "LINTER ERRORS:\n" + "\n".join(str(e) for e in hard_errors)
                feedback += "\n\nFix ALL errors. Output ONLY raw TypeScript code."
            else:
                print("Max retries reached.")

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
    print(f"\nSuccess: {result['success']} | Attempts: {result['attempts']}")
    print(result["code"])
