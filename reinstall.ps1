$components = "api","platform","data_source_plugin-1","data_source_plugin-2","simple_visualizer","block_visualizer"

pip uninstall -y graph-platform graph-source-one graph-source-two graph-viz-simple graph-viz-block graph-api

foreach ($c in $components) {
    foreach ($n in "build","dist") { Remove-Item -Recurse -Force "$c\$n" -ErrorAction SilentlyContinue }
    Get-ChildItem $c -Directory -Filter *.egg-info | Remove-Item -Recurse -Force
}

foreach ($c in $components) { pip install ".\$c" }
