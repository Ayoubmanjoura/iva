from actions._music import get_tracks, find_closest, play
 
 
def run(args):
    query = args.get("query", "").strip()
    tracks = get_tracks()
 
    if not tracks:
        return "No tracks found in the playlist."
 
    if not query:
        # Play full playlist from the beginning
        play(index=0)
        return f"Playing your playlist. {len(tracks)} tracks loaded."
 
    # Fuzzy match against playlist titles
    index = find_closest(query)
    if index is None:
        # Closest match fallback — just pick track 0 (guaranteed)
        index = 0
 
    play(index=index)
    return f"Playing {tracks[index]['title']}."
 