-- Map fenced divs (::: tip / note / warning / plain / do / dont / cheatsheet /
-- pullquote) to the tcolorbox environments defined in preamble.tex.
local env = {
  tip        = "protip",
  protip     = "protip",
  note       = "anchorbox",
  anchor     = "anchorbox",
  warning    = "warningbox",
  plain      = "plainbox",
  ["do"]     = "dobox",
  dont       = "dontbox",
  cheatsheet = "cheatsheetbox",
  alert      = "cheatsheetbox",
  pullquote  = "pullquote",
}

function Div(el)
  for _, cls in ipairs(el.classes) do
    local e = env[cls]
    if e then
      local out = {}
      table.insert(out, pandoc.RawBlock("latex", "\\begin{" .. e .. "}"))
      for _, blk in ipairs(el.content) do
        table.insert(out, blk)
      end
      table.insert(out, pandoc.RawBlock("latex", "\\end{" .. e .. "}"))
      return out
    end
  end
  return nil
end
