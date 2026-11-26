import re

def verify_candidate():
    with open("test_candidate.svg", "r") as f:
        svg = f.read()

    # Check title lines length
    title_matches = re.findall(r'<tspan[^>]*>(.*?)</tspan>', svg[:1000])
    print("Title tspans:", title_matches[:2])
    for tm in title_matches[:2]:
        print(f"Title line: '{tm}', length={len(tm)} chars")
        assert len(tm) <= 45, f"Title line too long: {tm}"

    # Check orange color count
    # Only #db8129 or orange should be used for the single most important item
    orange_matches = re.findall(r'#db8129', svg)
    print(f"Orange #db8129 occurrences: {len(orange_matches)}")
    # In payoff box: stroke="#db8129", fill="#db8129" for text
    # Should be strictly for the payoff
    assert 1 <= len(orange_matches) <= 3, f"Unexpected orange count: {len(orange_matches)}"

    # Check that no <marker> arrows exist, or count arrows
    arrows = re.findall(r'<marker', svg)
    print(f"Arrow markers: {len(arrows)}")
    arrow_paths = re.findall(r'marker-end', svg)
    print(f"Arrows used: {len(arrow_paths)}")
    assert len(arrow_paths) == 0, "No arrows were in source, but found arrow references!"

    # Check that all text elements are >= 24px
    font_sizes = [float(x) for x in re.findall(r'font-size="(\d+(?:\.\d+)?)"', svg)]
    print(f"Min font size: {min(font_sizes)}, Max font size: {max(font_sizes)}")
    assert min(font_sizes) >= 24, "Font size smaller than 24px found!"

    print("All candidate sanity checks passed successfully!")

if __name__ == "__main__":
    verify_candidate()
