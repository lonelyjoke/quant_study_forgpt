def summarize(numbers):
    total = sum(numbers)
    average = total / len(numbers)
    return {
        "count": len(numbers),
        "total": total,
        "average": average,
        "minimum": min(numbers),
        "maximum": max(numbers),
    }


def main():
    sample = [3, 7, 11, 18, 23]
    stats = summarize(sample)

    print("Codex code test succeeded.")
    print(f"Input numbers: {sample}")
    print(
        "Summary: "
        f"count={stats['count']}, "
        f"total={stats['total']}, "
        f"average={stats['average']:.2f}, "
        f"min={stats['minimum']}, "
        f"max={stats['maximum']}"
    )


if __name__ == "__main__":
    main()
