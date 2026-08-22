# theme.py
# Centralized formatting and styling for OsdagBridge LaTeX Reports

# Colors
OSDAG_GREEN = "91B014"
RED_FAIL = "red"
BLACK_PASS = "black"

# Table Spacing & Padding
TABLE_COL_SEP = "6pt"
ARRAY_STRETCH = "1.12"
LONGTABLE_PRE = "0pt"
LONGTABLE_POST = "6pt"
RULE_WIDTH = "0.5pt"
EXTRA_ROW_HEIGHT = "0.6pt"

# Table Helpers
def lt_header(headers_tex: str, caption: str = "") -> str:
    """
    Returns the \endfirsthead and \endhead LaTeX definitions for a longtable
    to ensure headers repeat properly across page breaks.
    """
    cap_tex = f"\\caption{{{caption}}} \\\\\n" if caption else ""
    cont_cap_tex = f"\\caption*{{{caption} (Continued)}} \\\\\n" if caption else ""
    
    return f"""
{cap_tex}\\toprule
{headers_tex} \\\\
\\midrule
\\endfirsthead

{cont_cap_tex}\\toprule
{headers_tex} \\\\
\\midrule
\\endhead

\\bottomrule
\\endfoot

\\bottomrule
\\endlastfoot
"""
