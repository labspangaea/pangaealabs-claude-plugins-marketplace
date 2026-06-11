# Example prompt

```
Make a concept-deck PDF from rag-system-design.md, branded as Pangaea Digital Labs.
```

This renders the `concept-deck` template end to end — a **technical-doc, SVG-first** 16:9
deck (ByteByteGo idiom). Each concept is **one hand-written full-canvas `1920×1080` SVG**
(`figure full`): flat near-white field, heavy black Poppins titles, black-outlined
multi-pastel cards, **black** orthogonal connectors, sticker icons, signal-blue accent.

The 9 slides: a `cover`, then six full-canvas SVG concepts — *RAG, end to end* (a dense
**2×2 framed-panel composite**) → *Without RAG, it guesses* → *The RAG architecture*
(5-node loop) → *The RAG pipeline* (4 stages) → the 12-icon sticker kit → *The RAG
lifecycle* (a **3-lane swim-lane pipeline** with a feedback loop) — then the one navy
`statement` and a `closing`. The chrome is deliberately minimal; the SVG is the content,
and a `figure full` SVG has no complexity ceiling. SVG-DNA generation spec:
[`../../assets/templates/concept-deck/icons.md`](../../assets/templates/concept-deck/icons.md).
