if "JSON_LOCAL_ENV" in $env {
  open $env.JSON_LOCAL_ENV | load-env
}

def main [] {
  print 'pymecli script'
}

def "main bnsync" [] {
  uv run binance sync
}

def "main px" [symbols: string = "btcusdt,ethusdt,pepeusdt"] {
  uv run binance spot $symbols
  uv run okx spot $symbols
  uv run bitget spot $symbols
  uv run gate spot $symbols
}
