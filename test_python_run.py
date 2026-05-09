message = "Hello Codex Python"
total = sum(range(1, 101))

output = f"{message}\nSum 1 to 100: {total}\n"

print(message)
print(f"Sum 1 to 100: {total}")

with open("python_run_result.txt", "w", encoding="utf-8") as result_file:
    result_file.write(output)
