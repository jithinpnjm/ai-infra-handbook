from PIL import Image

img = Image.open("investigation_ladder.png")
print("Image dimensions:", img.size)
print("Image mode:", img.mode)
