data = b'W\x92\x80\x00\x00\x01\x00\x00\x00\x02\x00\x00\x07example\x03com\x00\x00\x02\x00\x01\xc0\x0c\x00\x02\x00\x01\x00\x02\xa3\x00\x00\x14\x01a\x0ciana-servers\x03net\x00\xc0\x0c\x00\x02\x00\x01\x00\x02\xa3\x00\x00\x04\x01b\xc0+'

# The pointer is at the last 2 bytes of the second NS RDATA: \xc0+
# In your bytes, \xc0\x2b (0x2b = 43)
pointer_offset_in_data = len(data) - 2  # last two bytes

# Read the pointer
pointer_bytes = data[pointer_offset_in_data:pointer_offset_in_data+2]
pointer_value = int.from_bytes(pointer_bytes, 'big')
target_offset = pointer_value & 0x3FFF  # remove first two bits

print(data[target_offset:])
# Read the text at the target offset
labels = []
while True:
    length = data[target_offset]
    if length == 0:
        break
    target_offset += 1
    label = data[target_offset:target_offset+length].decode('ascii')
    labels.append(label)
    target_offset += length

iana_server_name = '.'.join(labels)
print("Second NS points to:", iana_server_name)