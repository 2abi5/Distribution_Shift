-- For HTML/PDF output, use the vector (SVG) version of each figure when it exists.
function Image(img)
  if FORMAT:match("html") then
    local svg = img.src:gsub("%.png$", ".svg")
    local f = io.open(svg, "r")
    if f then f:close(); img.src = svg end
  end
  return img
end
