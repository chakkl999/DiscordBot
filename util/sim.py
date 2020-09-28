from PIL import Image
from io import BytesIO
import pathlib
from imagehash import average_hash
import asyncio
import aiohttp

BASEDIR = pathlib.Path(__file__).resolve().parent.parent

def getURL(file: str):
    with BASEDIR.joinpath("links", file+".txt").open(mode='r') as f:
        links = list(enumerate(list(map(str.strip, f.readlines())), start=1))
    return links

async def imageSimAsync(file, session):
    try:
        print("Getting images...")
        links = getURL(file)
    except Exception as e:
        print(f"Unable to open file: {e}")
        return
    images = await asyncio.gather(*[fetchImage(url, session) for url in links])
    print("Finished getting images.")

    hashes = []
    for image in images:
        hashes.append((image[0], average_hash(image[1])))
        image[1].close()
    print("Finished computing hashes.")

    print("Computing similarity...")
    similarity = []
    for i in range(len(hashes)):
        similarity.append([])
        for hash in hashes:
            similarity[i].append((hashes[i][0], hash[0], hashes[i][1] - hash[1]))
    print("Finished computing similarity.")
    print()

    seenpair = set()
    cutoff = 5
    for row in range(len(similarity)):
        for col in range(len(similarity[row])):
            if row != col:
                if similarity[row][col][2] <= cutoff:
                    if (row, col) not in seenpair:
                        print(f"Line {similarity[row][col][0]} is similar to line {similarity[row][col][1]} with a score of {similarity[row][col][2]}.")
                        seenpair.add((row, col))
                        seenpair.add((col, row))
    if not seenpair:
        print("Everything is clean (probably).")
    print()

async def fetchImage(url, session):
    async with session.get(url[1]) as r:
        image = Image.open(BytesIO(await r.read()))
    return (url[0], image)

def checklink(file: str):
    try:
        with BASEDIR.joinpath("links", file+".txt").open(mode='r') as f:
            links = list(map(str.strip, f.readlines()))
    except Exception as e:
        print(f"Unable to open file: {e}")
        return
    linkSet = set()
    dup = []
    i = 1
    for link in links:
        if link not in linkSet:
            linkSet.add(link)
        else:
            dup.append((i, link))
        i += 1
    if dup:
        print("\n".join([f"Line {link[0]}: {link[1]}" for link in dup]))
    else:
        print("It's clean")


def checkalllink():
        links = {}
        try:
            for file in BASEDIR.joinpath("links").glob("*.txt"):
                with file.open(mode="r") as f:
                    links[file.stem] = list(map(str.strip, f.readlines()))
        except Exception as e:
            print(f"Unable to open file: {e}")
            return
        linkSet = set()
        dup = {}
        i = 1
        for file, link in links.items():
            for l in link:
                if l not in linkSet:
                    linkSet.add(l)
                else:
                    if file in dup:
                        dup[file].append((i, l))
                    else:
                        dup[file] = [(i, l)]
                i += 1
            i = 1
        if dup:
            for file, linklist in dup.items():
                print(f"In {file}:")
                print("\n".join([f"Line {link[0]}: {link[1]}" for link in linklist]))
        else:
            print("All is clean.")

async def main():
    session = aiohttp.ClientSession()
    try:
        while True:
            which = int(input("Enter 1 for link check or 2 for image similarity check or 3 to exit: "))
            if which == 3:
                break
            file = str(input("Enter a file name(Enter 'all' for link check to check all file for dup): ")).upper()
            if which == 1:
                if file == "ALL":
                    checkalllink()
                else:
                    checklink(file)
            elif which == 2:
                await imageSimAsync(file, session)
            else:
                print("Not an option.")
    except Exception as e:
        print(e)
    await session.close()

if __name__ == "__main__":
    asyncio.run(main())
