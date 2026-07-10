class CompletenessValidator:
    def validate(self, scenario, required_form_codes: set[str], cash_flow_lines) -> tuple[bool, list[str]]:
        present = {line.form_code for line in cash_flow_lines}
        missing = sorted(required_form_codes - present)
        if not cash_flow_lines:
            missing = sorted(required_form_codes) or ["cash_flow_lines"]
        return not missing, missing
