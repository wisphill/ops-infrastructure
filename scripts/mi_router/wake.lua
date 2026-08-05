local socket = require("socket")

local udp = assert(socket.udp4())

-- turn on broadcast
assert(udp:setoption("broadcast", true))

--  Bind 0.0.0.0 to all interfaces
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
