local socket = require("socket")

local TOKEN = os.getenv("TOKEN")
local CHAT_ID = os.getenv("CHAT_ID")

local OFFSET_FILE = "/data/tg.offset"

-- fallback when running on the local
local function file_exists(path)
    local f = io.open(path, "r")
    if f then
        f:close()
        return true
    end
    return false
end

if not file_exists(OFFSET_FILE) then
    OFFSET_FILE = "tg.offset"
end

local function save_offset(offset)
    local f = io.open(OFFSET_FILE, "w")
    if f then
        f:write(tostring(offset))
        f:close()
    end
end

local function load_offset()
    local f = io.open(OFFSET_FILE, "r")

    if not f then
        save_offset(0)
        return 0
    end

    local offset = tonumber(f:read("*a")) or 0
    f:close()

    return offset
end

-- wol by sending magic pkg
function wake()
    local udp = assert(socket.udp4())
    assert(udp:setoption("broadcast", true))
    assert(udp:setsockname("0.0.0.0", 0))

    -- MAC Target: 70:85:c2:7c:0f:c5
    local mac = string.char(0x70, 0x85, 0xc2, 0x7c, 0x0f, 0xc5)
    local payload = string.char(0xff):rep(6) .. string.rep(mac, 16)

    local ok, err = udp:sendto(payload, "192.168.1.255", 9)

    udp:close()
    if ok then
        print("Send Magic Packet to the server (70:85:c2:7c:0f:c5) successfully with Lua!")
    else
        print("Failed to send Magic Packet:", err)
    end
end

local offset = load_offset()

print("Telegram listener started...")
print("Using offset file:", OFFSET_FILE)

while true do
    local url = string.format(
        "https://api.telegram.org/bot%s/getUpdates?timeout=30&offset=%d",
        TOKEN,
        offset
    )

    -- run curl in silent mode
    local cmd = string.format("curl -s '%s'", url)

    local f = io.popen(cmd)
    local data = f:read("*a")
    f:close()

    if data and data ~= "" then
        -- debug raw response
        print("Telegram response:", data)

        -- debug chat id
        for chat_id in data:gmatch('"chat":%s*{%s*"id":(%d+)') do
            print("Chat ID:", chat_id)
        end

        -- debug message
        for text in data:gmatch('"text":"([^"]+)"') do
            print("Message:", text)
        end

        -- get my chat only
        if data:find('"id":' .. CHAT_ID, 1, true) then
            if data:find("/wake", 1, true) then
                print("Wake command received")
                wake()
            end
        end

        local last
        for id in data:gmatch('"update_id":(%d+)') do
            last = tonumber(id)
        end

        if last then
            offset = last + 1
            save_offset(offset)
        end
    else
        print("Telegram request failed or timed out.")
        socket.sleep(5)
    end

    socket.sleep(1)
end
