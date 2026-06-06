from app.engine.llm import generate_with_gemini


if __name__ == "__main__":
    output = generate_with_gemini(
        "Reply with exactly: SCK Gemini connection successful."
    )

    print(output)