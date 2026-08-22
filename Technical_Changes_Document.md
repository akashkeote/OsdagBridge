# Technical Changes Document
**Task:** OsdagBridge LaTeX Report Generator Refactoring & Enhancements

## 1. Key Code and LaTeX Modifications
- **LongTable Headers:** Developed a Python parsing script (`fix_tables2.py`) to systematically identify all `\begin{longtable}` environments across the report modules (`chap2.py`, `chap4.py`, `chap5.py`, `chap7.py`) and dynamically inject `\endfirsthead` and `\endhead` blocks. This ensures that column headers repeat flawlessly when tables span across multiple pages, significantly improving readability and preventing footer overlap.
- **Live Load Table Separation:** Refactored `chap3.py` to break down the monolithic loads table. The Vehicular Live Loads and Footpath Live Loads were separated into two distinct, clearly structured PyLaTeX tables.
- **Data Visualization Integration:** Created a dedicated Python module (`plots.py`) utilizing `matplotlib` to programmatically generate:
  - An **Overall Utilization Ratio (UR)** bar chart with a red dashed threshold line at `UR=1.0`.
  - **Material Quantity** bar charts comparing Structural Steel tonnage and Concrete volume vs. Reinforcement Steel weight.
- **Dynamic Embedding:** Updated `report_generator.py` to intercept the payload, generate the plots on-the-fly, save them to the temporary assets directory, and embed them directly into `chap5.py` and `chap7.py` using `\includegraphics`.

## 2. Specific Files Altered Under Report Generator
- `src/osdagbridge/core/reports/chap2.py` (Table headers refactored)
- `src/osdagbridge/core/reports/chap3.py` (Live Load split & headers refactored)
- `src/osdagbridge/core/reports/chap4.py` (Table headers refactored)
- `src/osdagbridge/core/reports/chap5.py` (Table headers refactored, UR plot embedded)
- `src/osdagbridge/core/reports/chap7.py` (Table headers refactored, Material plots embedded)
- `src/osdagbridge/core/reports/report_generator.py` (Payload interception and plot generation hooks added)
- `src/osdagbridge/core/reports/plots.py` **[NEW]** (Matplotlib plotting logic)
- `src/osdagbridge/core/reports/theme.py` **[NEW]** (Centralized style configuration)

## 3. Structure of the Centralized Formatting Configuration Module
The new `theme.py` module serves as the single source of truth for LaTeX document styling. It includes:
- **Color Palettes:** Predefined LaTeX color macros (e.g., `osdagGreen`).
- **Table Padding & Spacing:** Global variables for `\arraystretch` and `\tabcolsep`.
- **Header Generation Helpers:** A dedicated `lt_header()` function that dynamically generates uniform, styled `\rowcolor` headers and captions for any PyLaTeX LongTable.

## 4. Rationale for Architectural or Styling Choices
- **Decoupled Plotting:** By placing the plotting logic into an independent `plots.py` file, we prevent the core `report_generator.py` from becoming cluttered. It cleanly accepts data structures and returns file paths, adhering to separation of concerns.
- **Regex/String Parsing for Legacy Tables:** Instead of attempting to rewrite massive blocks of raw PyLaTeX strings into complex Python object trees, a targeted Python parsing approach was used to inject the `\endhead` headers. This minimized the risk of breaking existing structural logic while fulfilling the strict LaTeX pagination requirements.
- **Consistent Theming:** The `lt_header()` function drastically reduces boilerplate code in the chapter files. Future updates to Osdag's branding or table designs can now be implemented in a single line inside `theme.py` rather than altering 30+ tables individually.
