from data import library
from engine import recommend


def main():
    current = library[1]  # Try Jagö as current track
    print(f"\nCurrent Track: {current.artist} - {current.title}")
    print(f"BPM: {current.bpm} | Key: {current.key} | Energy: {current.energy}\n")

    results = recommend(current, library)

    for track, score in results:
        print(
            f"{track.artist} - {track.title} | "
            f"BPM: {track.bpm} | Key: {track.key} | "
            f"Energy: {track.energy} | Score: {score}"
        )


if __name__ == "__main__":
    main()
