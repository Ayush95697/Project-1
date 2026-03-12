import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from pymongo import MongoClient


def get_client() -> MongoClient:
    load_dotenv()
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    return MongoClient(uri)


def get_db():
    client = get_client()
    db_name = os.getenv("MONGODB_DB_NAME", "adaptive_diagnostic")
    return client[db_name]


def build_questions() -> List[Dict[str, Any]]:
    """
    Seed at least 20 GRE-style questions with a good spread of
    difficulties and topics.
    """
    return [
        {
            "_id": "q1",
            "question_text": "Solve for x: 2x + 3 = 11",
            "options": ["x=2", "x=3", "x=4", "x=5"],
            "correct_answer": "x=4",
            "difficulty": 0.3,
            "topic": "Algebra",
            "tags": ["linear equation", "basic algebra"],
        },
        {
            "_id": "q2",
            "question_text": "What is the value of 3/4 + 2/3?",
            "options": ["17/12", "13/12", "5/7", "1 1/3"],
            "correct_answer": "17/12",
            "difficulty": 0.2,
            "topic": "Arithmetic",
            "tags": ["fractions", "addition"],
        },
        {
            "_id": "q3",
            "question_text": "If y = 2x^2 and x = 3, what is y?",
            "options": ["12", "16", "18", "20"],
            "correct_answer": "18",
            "difficulty": 0.4,
            "topic": "Algebra",
            "tags": ["quadratic", "substitution"],
        },
        {
            "_id": "q4",
            "question_text": "A triangle has sides 3, 4, and 5. What type of triangle is it?",
            "options": ["Equilateral", "Isosceles", "Right", "Obtuse"],
            "correct_answer": "Right",
            "difficulty": 0.3,
            "topic": "Geometry",
            "tags": ["pythagorean", "triangle"],
        },
        {
            "_id": "q5",
            "question_text": "What is 15% of 260?",
            "options": ["26", "36", "39", "45"],
            "correct_answer": "39",
            "difficulty": 0.3,
            "topic": "Arithmetic",
            "tags": ["percentage"],
        },
        {
            "_id": "q6",
            "question_text": "Select the word that is most similar to 'mitigate'.",
            "options": ["worsen", "alleviate", "ignore", "create"],
            "correct_answer": "alleviate",
            "difficulty": 0.5,
            "topic": "Vocabulary",
            "tags": ["synonym"],
        },
        {
            "_id": "q7",
            "question_text": "If x - 5 = 2(x - 3), what is x?",
            "options": ["1", "3", "7", "11"],
            "correct_answer": "1",
            "difficulty": 0.5,
            "topic": "Algebra",
            "tags": ["linear equation"],
        },
        {
            "_id": "q8",
            "question_text": "The average of five numbers is 12. If four of the numbers are 10, 8, 14, and 16, what is the fifth number?",
            "options": ["8", "10", "12", "14"],
            "correct_answer": "12",
            "difficulty": 0.4,
            "topic": "Arithmetic",
            "tags": ["average"],
        },
        {
            "_id": "q9",
            "question_text": "A square has area 81. What is its perimeter?",
            "options": ["18", "27", "36", "54"],
            "correct_answer": "36",
            "difficulty": 0.4,
            "topic": "Geometry",
            "tags": ["area", "perimeter"],
        },
        {
            "_id": "q10",
            "question_text": "Which number is a solution to the inequality 3x - 2 > 7?",
            "options": ["x=2", "x=3", "x=4", "x=1"],
            "correct_answer": "x=4",
            "difficulty": 0.5,
            "topic": "Algebra",
            "tags": ["inequality"],
        },
        {
            "_id": "q11",
            "question_text": "If 5^x = 125, what is x?",
            "options": ["2", "3", "4", "5"],
            "correct_answer": "3",
            "difficulty": 0.6,
            "topic": "Algebra",
            "tags": ["exponents"],
        },
        {
            "_id": "q12",
            "question_text": "The ratio of cats to dogs is 3:5. If there are 24 dogs, how many cats are there?",
            "options": ["10", "12", "14", "15"],
            "correct_answer": "14",
            "difficulty": 0.4,
            "topic": "Arithmetic",
            "tags": ["ratio"],
        },
        {
            "_id": "q13",
            "question_text": "Select the word that is most opposite in meaning to 'prolific'.",
            "options": ["fertile", "barren", "productive", "abundant"],
            "correct_answer": "barren",
            "difficulty": 0.6,
            "topic": "Vocabulary",
            "tags": ["antonym"],
        },
        {
            "_id": "q14",
            "question_text": "What is the area of a circle with radius 3 (use π ≈ 3.14)?",
            "options": ["9.42", "18.84", "28.26", "36.00"],
            "correct_answer": "28.26",
            "difficulty": 0.5,
            "topic": "Geometry",
            "tags": ["area", "circle"],
        },
        {
            "_id": "q15",
            "question_text": "If 2x + y = 10 and x - y = 1, what is x?",
            "options": ["2", "3", "4", "5"],
            "correct_answer": "3",
            "difficulty": 0.7,
            "topic": "Algebra",
            "tags": ["simultaneous equations"],
        },
        {
            "_id": "q16",
            "question_text": "Which of the following numbers is NOT prime?",
            "options": ["11", "17", "21", "29"],
            "correct_answer": "21",
            "difficulty": 0.5,
            "topic": "Arithmetic",
            "tags": ["prime numbers"],
        },
        {
            "_id": "q17",
            "question_text": "In a sequence, each term is double the previous term. If the third term is 12, what is the fifth term?",
            "options": ["24", "36", "48", "96"],
            "correct_answer": "48",
            "difficulty": 0.6,
            "topic": "Algebra",
            "tags": ["sequences"],
        },
        {
            "_id": "q18",
            "question_text": "A rectangle has a perimeter of 30 and length 9. What is its area?",
            "options": ["33", "54", "63", "72"],
            "correct_answer": "54",
            "difficulty": 0.6,
            "topic": "Geometry",
            "tags": ["perimeter", "area"],
        },
        {
            "_id": "q19",
            "question_text": "If the probability of an event is 0.2, what are the odds against the event?",
            "options": ["1:4", "4:1", "2:3", "3:2"],
            "correct_answer": "4:1",
            "difficulty": 0.8,
            "topic": "Logic",
            "tags": ["probability"],
        },
        {
            "_id": "q20",
            "question_text": "If f(x) = 2x^2 - 3x + 1, what is f(4)?",
            "options": ["21", "23", "25", "27"],
            "correct_answer": "21",
            "difficulty": 0.7,
            "topic": "Algebra",
            "tags": ["functions"],
        },
        {
            "_id": "q21",
            "question_text": "A statement is: 'If it rains, then the ground is wet.' Which of the following is the contrapositive?",
            "options": [
                "If the ground is wet, then it rains.",
                "If it does not rain, then the ground is not wet.",
                "If the ground is not wet, then it did not rain.",
                "If it rains, then the ground is not wet.",
            ],
            "correct_answer": "If the ground is not wet, then it did not rain.",
            "difficulty": 0.9,
            "topic": "Logic",
            "tags": ["implication", "contrapositive"],
        },
        {
            "_id": "q22",
            "question_text": "Select the word that best completes the sentence: "
            "'Her explanation was so _____ that everyone left more confused than before.'",
            "options": ["lucid", "opaque", "succinct", "concise"],
            "correct_answer": "opaque",
            "difficulty": 0.8,
            "topic": "Vocabulary",
            "tags": ["sentence completion"],
        },
    ]


def main() -> None:
    db = get_db()
    coll = db["questions"]
    questions = build_questions()
    for q in questions:
        coll.replace_one({"_id": q["_id"]}, q, upsert=True)
    coll.create_index("difficulty")
    print(f"Seeded {len(questions)} questions.")


if __name__ == "__main__":
    main()

