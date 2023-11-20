import numpy as np

from threefish import ThreeFish

np.seterr(all='ignore')


def text_to_blocks(text: str, block_size: int):
    bytes_ = text.encode()
    blocks = []
    for i in range(0, len(bytes_), block_size):
        block = bytes_[i:i + block_size]
        if len(block) < block_size:
            block += b'\x00' * (block_size - len(block))
        blocks.append(block)
    return blocks


# small test
print("Small test")
initial_text = "Do you know about atomic bomb?00"
np.seterr(all='ignore')
threeFish = ThreeFish(256)
encrypted = threeFish.encrypt("94dceb63801a3ca6aee5e949f7373950", "fbfdc5f401c4cf2f", initial_text)
encrypted = np.uint64(encrypted)
decrypted = threeFish.de_crypt("94dceb63801a3ca6aee5e949f7373950", "fbfdc5f401c4cf2f", encrypted)
decrypted = np.uint64(decrypted)
print("     Initial text:")
print(initial_text.encode())
print("     Encrypted text:")
print(encrypted.tobytes())
print("     Decrypted text:")
print(decrypted.tobytes())
print("")
# big test
print("Big test")
for i in range(0, 15):
    initial_text += initial_text
blocks = text_to_blocks(initial_text, 32)
encrypted_blocks = []
for block in blocks:
    encrypted_blocks.append(threeFish.encrypt("94dceb63801a3ca6aee5e949f7373950", "fbfdc5f401c4cf2f", block.decode()))
print("     Initial text:")
print(initial_text[:128].encode())
print("     Encrypted text:")
block = np.uint64(encrypted_blocks[:4])
print(block.tobytes())
print("     Decrypted text:")
decrypted_blocks = []
for block in encrypted_blocks:
    decrypted_blocks.append(threeFish.de_crypt("94dceb63801a3ca6aee5e949f7373950", "fbfdc5f401c4cf2f", block))
block = np.uint64(decrypted_blocks[:4])
print(block.tobytes())
