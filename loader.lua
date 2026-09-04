--[[
    xrio universal loader
    Reads _G._XRIO_KEY (set by the one-liner from the dashboard),
    fetches script.lua from the broker over the public Cloudflare tunnel,
    and executes it. No per-customer file, no embedded secrets.

    Usage (paste in executor) — the ..tick() is REQUIRED, not decoration:
    executors cache HttpGet by URL and ignore Cache-Control, so a fixed URL
    keeps serving a months-old copy of this file with a dead BROKER baked in.
        _G._XRIO_KEY="xrio_xxx";loadstring(game:HttpGet("https://xrio-web.vercel.app/loader.lua?v="..tick()))()
]]
local BROKER = "https://thank-handle-julie-demonstrates.trycloudflare.com"  -- auto-synced by auto_sync_tunnel.py

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

-- Base64 + the broker's keystream. The script used to come back as plaintext to
-- anyone holding a key, and signup is free and self-serve, so the source was a
-- 30-second fetch away and a saved URL kept working forever. Now it takes a
-- ticket: single use, seconds to live, bound to the IP that asked. Nothing here
-- stops someone dumping the source from inside their own executor — that is not
-- preventable, the interpreter needs plaintext eventually — but it does mean
-- the network is no longer a way in.
local B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
local function b64decode(str)
    str = str:gsub("[^" .. B64 .. "=]", "")
    local out, bits, count = {}, 0, 0
    for i = 1, #str do
        local c = str:sub(i, i)
        if c ~= "=" then
            bits = bits * 64 + (B64:find(c, 1, true) - 1)
            count = count + 6
            if count >= 8 then
                count = count - 8
                local byte = math.floor(bits / 2 ^ count) % 256
                out[#out + 1] = string.char(byte)
                bits = bits % (2 ^ count)
            end
        end
    end
    return table.concat(out)
end

-- Same keystream the broker uses; must stay byte-identical to _keystream_xor.
-- Plain bit32 arithmetic because no executor ships a crypto library we can
-- rely on. This was a MINSTD LCG taking the low 8 bits of the state, which a
-- listener could unwind from known plaintext (script.lua has a fixed header).
-- xorshift32 has no modular multiply to invert, and every output byte folds
-- all four bytes of the state, so no window of the state is exposed raw.
local function unmask(data, k, nonce)
    local bx, ls, rs, ba = bit32.bxor, bit32.lshift, bit32.rshift, bit32.band
    local function xs(x)
        x = bx(x, ls(x, 13))
        x = bx(x, rs(x, 17))
        x = bx(x, ls(x, 5))
        return x
    end
    local seed = 0x9E3779B9
    for i = 1, #k do seed = xs(bx(seed, k:byte(i))) end
    seed = xs(xs(bx(seed, nonce)))
    if seed == 0 then seed = 0x1F123BB5 end
    local out = {}
    for i = 1, #data do
        seed = xs(seed)
        local pad = ba(bx(seed, rs(seed, 8), rs(seed, 16), rs(seed, 24)), 0xFF)
        out[i] = string.char(bx(data:byte(i), pad))
    end
    return table.concat(out)
end

-- Hand the transport to the dispatch stage rather than letting it carry its own
-- copy. The keystream has to stay byte-identical to the broker's
-- _keystream_xor, and two copies of that in two files is a drift waiting to
-- happen — the failure would be a module that decodes to garbage, which
-- presents as a compile error with nothing pointing back at the cause.
-- Nothing new is exposed: _G._XRIO_KEY is already there.
_G._XRIO_FETCH  = fetch
_G._XRIO_B64DEC = b64decode
_G._XRIO_UNMASK = unmask

local cb = tostring(math.random(1, 2^31 - 1)) .. "_" .. tostring(os.time())
local tbody = fetch(BROKER .. "/api/ticket?key=" .. key .. "&_t=" .. cb)
local ticket, nonce
if type(tbody) == "string" then
    ticket = tbody:match('"ticket"%s*:%s*"(%x+)"')
    nonce  = tonumber(tbody:match('"nonce"%s*:%s*(%d+)'))
end
if not (ticket and nonce) then
    if writefile then
        pcall(writefile, "xrio_loader.txt",
            os.date("%H:%M:%S") .. " NO TICKET: " .. tostring(tbody):sub(1, 150))
    end
    warn("[xrio] could not get a ticket — is the broker up?")
    return
end

-- Tell the broker which game this is. xrio serves a set now, not one script,
-- and this is what keeps a Prison Life player from downloading the Blox Strike
-- module. Both ids are sent because they answer different questions: GameId
-- names the universe and survives places being added or renamed, PlaceId names
-- the one place. A broker that recognises neither replies with a dispatch
-- module that fingerprints the game client-side, so an old cached copy of this
-- loader — which sends neither — still works, just one round trip slower.
_G._XRIO_BROKER = BROKER   -- the dispatch stage refetches through this
local place, universe = "", ""
pcall(function() place = tostring(game.PlaceId or "") end)
pcall(function() universe = tostring(game.GameId or "") end)

local url = BROKER .. "/api/script?key=" .. key .. "&ticket=" .. ticket
    .. "&place=" .. place .. "&universe=" .. universe .. "&_t=" .. cb
local body, code = fetch(url)
if type(body) == "string" and #body > 100 and not body:match("^%-%-") then
    body = unmask(b64decode(body), key, nonce)
end
-- Accumulate. This used to overwrite the file on every call, so the only line
-- that ever survived was the last one — and when the last one was a failure the
-- fetch length and decode state that would have explained it were already gone.
local _rlog = {}
local function report(msg)
    _rlog[#_rlog + 1] = os.date("%H:%M:%S") .. " " .. msg
    if writefile then pcall(writefile, "xrio_loader.txt", table.concat(_rlog, "\n")) end
    warn("[xrio] " .. msg)
end
report(("fetched code=%s len=%s head=%q"):format(
    tostring(code), tostring(body and #body or 0),
    tostring(body and body:sub(1, 24) or "")))

if not body or #body < 100 then
    report(("FETCH FAILED code=%s len=%s"):format(tostring(code), tostring(body and #body or 0)))
    return
end
if code == 401 or body:sub(1, 10) == "-- xrio: k" then
    report("AUTH REJECTED " .. body:sub(1, 150))
    return
end

-- Three returns, not two. loadstring signals a compile error by returning
-- `nil, message`, so pcall hands back `true, nil, message` — binding only two
-- names threw the message away and every failure reported the useless
-- "LOADSTRING FAILED: nil".
local ok, loaded, lerr = pcall(loadstring, body)
if not ok or type(loaded) ~= "function" then
    report(("LOADSTRING FAILED ok=%s type=%s err=%s"):format(
        tostring(ok), type(loaded), tostring(lerr or loaded):sub(1, 400)))
    return
end
local ok2, err = pcall(loaded)
if not ok2 then
    report("SCRIPT CRASHED: " .. tostring(err):sub(1, 300))
else
    report("script returned normally")
end
