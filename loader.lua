--[[
    xrio universal loader
    Reads _G._XRIO_KEY (set by the one-liner from the dashboard),
    fetches script.lua from the broker over the public Cloudflare tunnel,
    and executes it. No per-customer file, no embedded secrets.

    Usage (paste in executor):
        _G._XRIO_KEY="xrio_xxx";loadstring(game:HttpGet("https://xrio-web.vercel.app/loader.lua"))()
]]
local BROKER = "https://respectively-sms-expired-lenses.trycloudflare.com"  -- auto-synced by auto_sync_tunnel.py

local key = (_G._XRIO_KEY or ""):gsub("%s+", "")
if key == "" then
    warn("[xrio] no key. Get one from the xrio dashboard and paste the full one-liner.")
    return
end
-- script.lua reads _G._XRIO_COMPANION_KEY for WebSocket auth; mirror the same key.
_G._XRIO_COMPANION_KEY = key

-- Cache-busted GET via request() (executor's HTTP can't reach localhost but reaches tunnels fine)
local req = request or http_request or (syn and syn.request)
local function fetch(url)
    if req then
        local ok, res = pcall(function() return req({Url=url, Method="GET"}) end)
        if ok and type(res) == "table" then
            return (res.Body or res.body), (res.StatusCode or res.status_code or res.Status)
        end
    end
    local ok, body = pcall(game.HttpGet, game, url)
    if ok then return body, 200 end
    return nil, nil
end

local cb = tostring(math.random(1, 2^31 - 1)) .. "_" .. tostring(os.time())
local url = BROKER .. "/api/script?key=" .. key .. "&_t=" .. cb
local body, code = fetch(url)

if not body or #body < 100 then
    warn(("[xrio] couldn't fetch script (code=%s len=%s)"):format(
        tostring(code), tostring(body and #body or 0)))
    return
end
if code == 401 or body:sub(1, 10) == "-- xrio: k" then
    warn("[xrio] " .. body:sub(1, 200))
    return
end

local ok, loaded = pcall(loadstring, body)
if not ok or type(loaded) ~= "function" then
    warn("[xrio] loadstring failed: " .. tostring(loaded):sub(1, 200))
    return
end
local ok2, err = pcall(loaded)
if not ok2 then
    warn("[xrio] script crashed during init: " .. tostring(err):sub(1, 300))
end
