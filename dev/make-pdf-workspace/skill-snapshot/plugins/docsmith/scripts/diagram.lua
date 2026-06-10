-- docsmith pandoc filter (handbook / pandoc-tectonic backend).
-- Replaces each ```d2 code block with the pre-rendered PDF diagram from the
-- shared manifest (env DOCSMITH_DIAG_MANIFEST), in document order, reusing the
-- handbook preamble's \dgram{file}{opts}{caption} helper for consistent styling.

local diagrams = nil
local idx = 0

local function load()
  if diagrams ~= nil then return end
  diagrams = {}
  local path = os.getenv("DOCSMITH_DIAG_MANIFEST")
  if not path then return end
  local fh = io.open(path, "r")
  if not fh then return end
  local raw = fh:read("*a")
  fh:close()
  local ok, dec = pcall(pandoc.json.decode, raw)
  if ok and dec and dec.diagrams then diagrams = dec.diagrams end
end

local function tex_escape(s)
  s = s:gsub("\\", "\\textbackslash{}")
  s = s:gsub("([&%%$#_{}])", "\\%1")
  s = s:gsub("~", "\\textasciitilde{}")
  s = s:gsub("%^", "\\textasciicircum{}")
  return s
end

function CodeBlock(el)
  if not el.classes:includes("d2") then return nil end
  load()
  idx = idx + 1
  local d = diagrams[idx]
  if not d then return nil end
  local cap = tex_escape(d.caption or "")
  local tex = "\\dgram{" .. d.pdf .. "}{width=0.85\\linewidth}{" .. cap .. "}"
  return pandoc.RawBlock("latex", tex)
end
