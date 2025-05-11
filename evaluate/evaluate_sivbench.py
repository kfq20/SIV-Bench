import json
import re
import string
from collections import defaultdict
import os
import pickle
import argparse # Import the argparse library
import copy

# MODEL = "gemini-2.5-flash-preview-04-17" # Original model (can be overridden by command-line arg)
# TYPE = "no_sub" # Original type (can be overridden by command-line arg)

QA_SRC_PATH = "evaluate/QA_src.json"
LETTER_TO_INDEX = {
    "A": 0,
    "B": 1,
    "C": 2,
    "D": 3,
    "E": 4,
    "F": 5,
    "G": 6,
    "H": 7,
    "I": 8,
    "J": 9,
    "K": 10,
    "L": 11,
    "M": 12,
    "N": 13,
}

def convert_pickle_to_json(pickle_file_path, json_file_path):
    """
    Convert a pickle file to a JSON file.
    
    Args:
        pickle_file_path (str): Path to the input pickle file.
        json_file_path (str): Path to the output JSON file.
    """
    try:
        with open(pickle_file_path, 'rb') as f:
            data = pickle.load(f)
        
        with open(json_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
        
        print(f"Successfully converted {pickle_file_path} to {json_file_path}")
    except Exception as e:
        print(f"Error: {e}")

    return data

def split_answer_string(answer_string, original_questions):
    parsed_answers = {}
    has_q_format = False
    lines = answer_string.strip().split('\n')
    processed_indices = set()

    pattern = re.compile(r"Q(\d+):\s*(.*?)(?=\nQ\d+:|\Z)", re.IGNORECASE | re.DOTALL)
    pattern_2 = re.compile(r"A(\d+):\s*(.*?)(?=\nA\d+:|\Z)", re.IGNORECASE | re.DOTALL)
    pattern_3 = re.compile(r"(\d+)\.\s*(.*?)(?=\n\d+\.\s|\Z)", re.DOTALL)
    matches = pattern.findall(answer_string)
    matches_2 = pattern_2.findall(answer_string)
    matches_3 = pattern_3.findall(answer_string)

    if matches:
        has_q_format = True
        for match in matches:
            try:
                q_index = int(match[0]) - 1 # Convert Q number to 0-based index
                answer_text = match[1].strip()
                if 0 <= q_index < len(original_questions):
                    question_text = original_questions[q_index]
                    parsed_answers[question_text] = answer_text
                    processed_indices.add(q_index)
                else:
                    print(f"Warning: Q number {match[0]} out of range for questions: {original_questions}")
                    # If index is out of range, parsing is unreliable, fall back to raw
                    return {}, answer_string
            except ValueError:
                 print(f"Warning: Could not parse Q number from match: {match}")
                 return {}, answer_string # Fallback if Q number isn't an int
            except Exception as e:
                print(f"Warning: Error parsing match '{match}': {e}")
                return {}, answer_string # General fallback

        # Check if all original questions were covered if Q format was found
        if len(parsed_answers) != len(original_questions) and len(original_questions) > 0:
             print(f"Warning: Mismatch between parsed answers ({len(parsed_answers)}) and original questions ({len(original_questions)}) for answer string: {answer_string}")
             # Decide if fallback is needed. Maybe only if *no* matches were found?
             # Let's stick with parsed for now, but keep raw as secondary option.  
    
    elif matches_2:
        has_q_format = True
        for match in matches_2:
            try:
                q_index = int(match[0]) - 1 # Convert Q number to 0-based index
                answer_text = match[1].strip()
                if 0 <= q_index < len(original_questions):
                    question_text = original_questions[q_index]
                    parsed_answers[question_text] = answer_text
                    processed_indices.add(q_index)
                else:
                    print(f"Warning: Q number {match[0]} out of range for questions: {original_questions}")
                    # If index is out of range, parsing is unreliable, fall back to raw
                    return {}, answer_string
            except ValueError:
                 print(f"Warning: Could not parse Q number from match: {match}")
                 return {}, answer_string # Fallback if Q number isn't an int
            except Exception as e:
                print(f"Warning: Error parsing match '{match}': {e}")
                return {}, answer_string # General fallback

        # Check if all original questions were covered if Q format was found
        if len(parsed_answers) != len(original_questions) and len(original_questions) > 0:
             print(f"Warning: Mismatch between parsed answers ({len(parsed_answers)}) and original questions ({len(original_questions)}) for answer string: {answer_string}")
             # Decide if fallback is needed. Maybe only if *no* matches were found?
             # Let's stick with parsed for now, but keep raw as secondary option. 

    elif matches_3:
        has_q_format = True
        for match in matches_3:
            try:
                q_index = int(match[0]) - 1 # Convert Q number to 0-based index
                answer_text = match[1].strip()
                if 0 <= q_index < len(original_questions):
                    question_text = original_questions[q_index]
                    parsed_answers[question_text] = answer_text
                    processed_indices.add(q_index)
                else:
                    print(f"Warning: Q number {match[0]} out of range for questions: {original_questions}")
                    # If index is out of range, parsing is unreliable, fall back to raw
                    return {}, answer_string
            except ValueError:
                 print(f"Warning: Could not parse Q number from match: {match}")
                 return {}, answer_string
        # Check if all original questions were covered if Q format was found
        if len(parsed_answers) != len(original_questions) and len(original_questions) > 0:
             print(f"Warning: Mismatch between parsed answers ({len(parsed_answers)}) and original questions ({len(original_questions)}) for answer string: {answer_string}")
             # Decide if fallback is needed. Maybe only if *no* matches were found?
             # Let's stick with parsed for now, but keep raw as secondary option.
        
    # If no "Q<number>:" format was found, and there's exactly one question
    elif not has_q_format and len(original_questions) == 1:
        question_text = original_questions[0]
        parsed_answers[question_text] = answer_string.strip()

    # If parsing failed, or format is ambiguous (e.g., no Q numbers but multiple questions)
    # Return empty parsed dict and the raw string as fallback
    if not parsed_answers and original_questions:
        print(f"Warning: Could not reliably parse answers or ambiguity detected. Using raw answer for: {answer_string}")
        return {}, answer_string
    elif not original_questions and answer_string:
         print(f"Warning: Received answers but no original questions found for a video? Raw answer: {answer_string}")
         return {}, answer_string # Fallback


    # Return parsed answers, and potentially the raw string if parsing was partial/weird
    # Let's return raw string only if parsing completely failed or was ambiguous (handled above)
    # If parsing succeeded (even partially), don't provide raw string as primary fallback
    # But maybe provide it *in addition*? Let's return raw string for *all* cases where parsing was attempted
    # so the caller can decide. Let's refine: return raw only if parsing failed/ambiguous.
    if not parsed_answers and original_questions: # Condition for fallback already checked above
        return {}, answer_string
    else:
        # If we successfully parsed *something*, return parsed + None fallback
        # If we had Q format but it didn't match count, it's still parsed.
        return parsed_answers, None
    
def parse_model_answers(qa_src_data, model_answer):
    all_qa_questions_map = {}
    for item in qa_src_data:
        video_path = item.get("video_path")
        qa_pairs_data = item.get("QA_pairs", {}).get("qa_pairs", [])
        if not video_path or not qa_pairs_data:
            continue
        all_qa_questions_map[video_path] = [qa.get("question") for qa in qa_pairs_data if qa.get("question")]
    
    parsed_model_answers = {}
    for video_path, answer_string in model_answer.items():
        original_questions = all_qa_questions_map.get(video_path, [])
        if not original_questions:
            print(f"Warning: No original questions found in all_qa.json for path: {video_path}. Storing raw answer.")
            parsed_model_answers[video_path] = ({}, answer_string) # Store raw answer if no questions to map to
            continue
            
        # Ensure answer_string is actually a string before parsing
        if isinstance(answer_string, str):
            parsed_q_to_a, raw_fallback = split_answer_string(answer_string, original_questions)
            parsed_model_answers[video_path] = (parsed_q_to_a, raw_fallback)
        else:

            print(f"Warning: Expected string answer for {video_path}, got {type(answer_string)}. Value: {answer_string}. Storing as raw.")
            # Store the non-string value as the 'raw' fallback directly
            parsed_model_answers[video_path] = ({}, str(answer_string)) # Convert to string just in case

    answer_data = copy.deepcopy(qa_src_data)
    for item in answer_data:
        video_path = item.get("video_path")
        if not video_path:
            continue
        q_to_a_map, raw_answer_fallback = parsed_model_answers.get(video_path, ({}, None))
        qa_pairs_list = item.get("QA_pairs", {}).get("qa_pairs", [])
        if not qa_pairs_list:
            continue

        for qa_pair in qa_pairs_list:
            question_text = qa_pair.get("question")
            if not question_text:
                qa_pair["model_answer"] = "Error: QA pair has no question text"
                continue
            specific_answer = q_to_a_map.get(question_text)
            if specific_answer:
                qa_pair["model_answer"] = specific_answer
            elif raw_answer_fallback is not None:
                # If specific answer not found, but we have a raw fallback for the video
                qa_pair["model_answer"] = raw_answer_fallback
                print(f"Info: Using raw fallback answer for question in {video_path}: '{question_text[:50]}...'")
            else:
                qa_pair["model_answer"] = "Error: Specific answer not found or parsed, and no raw fallback available."
                if video_path in parsed_model_answers and raw_answer_fallback is None:
                    qa_pair["model_answer"] = "Error: Answer parsing successful but did not include this specific question."

    return answer_data

def is_correct(pred, answer, correct_answer_index):
    # Remove punctuation, keep only words, ignore case
    if answer.lower() in pred.lower():
        return True
    else:
        # Extract the first letter of the first word in pred (uppercase) as the predicted answer letter
        # and remove any non-alphanumeric characters first
        cleaned_pred_parts = re.sub(r'[^\w\s]', '', pred).split()
        if not cleaned_pred_parts: # Handle cases where pred might be empty after cleaning
            return False
        pred_letter = cleaned_pred_parts[0][0].upper()
        # Convert letter to index
        pred_index = LETTER_TO_INDEX.get(pred_letter, -1)
        # Check if the index matches
        if pred_index == correct_answer_index:
            return True
    return False

def main():
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Evaluate model QA performance.")
    parser.add_argument(
        "--output_file",
        type=str,
        default="output/GPT-4o_SIV-Bench.pkl",
        help="Template for the input pkl file path. {MODEL} will be replaced."
    )
    args = parser.parse_args()
    output_pkl_path = args.output_file
    output_raw_data = convert_pickle_to_json(output_pkl_path, output_pkl_path.replace('.pkl', '.json'))
    
    with open(QA_SRC_PATH, 'r', encoding='utf-8') as f:
        qa_src_data = json.load(f)

    output_parsed_data = parse_model_answers(qa_src_data, output_raw_data)
    correct_count = 0
    wrong_items = []
    total_valid_data_num = 0

    for item in output_parsed_data:
        qa_pairs = item.get("QA_pairs", {}).get("qa_pairs", [])
        for qa_pair in qa_pairs:
            model_answer = qa_pair.get("model_answer")
            # Skip if model_answer is None or contains "Error"
            if model_answer is None or "Error" in model_answer:
                continue

            pred = model_answer.rstrip(string.punctuation)
            answer = qa_pair.get("answer", "").rstrip(string.punctuation) # Ensure answer is a string
            answer_index = qa_pair.get("correct_answer_index", 0) # Default to 0 if not present

            # Assuming 'level' comes from qa_pair, like other fields.
            # If 'level' is a global filter or from 'item', adjust this part.
            level_value = qa_pair.get("level", "") # Get level from qa_pair, default to empty string

            # Skip if level is empty or None after cleaning (original logic)
            if not level_value: # Handles None, empty string
                continue
            
            # The original code had 'level' being used without prior assignment in the loop.
            # If 'level' was meant to be 'level_value' from qa_pair:
            # level_cleaned = re.sub(r'[^\w\s]', '', str(level_value)).lower() # Ensure level_value is string
            # if not level_cleaned: # Check if empty after cleaning
            # continue
            # This 'level' check part seems to be what you intended, but its exact logic
            # might need to be clarified based on your data structure for 'level'.
            # For now, I'll keep the original logic of skipping if `level_value` is empty or None.

            is_correct_answer = is_correct(pred, answer, answer_index)
            if is_correct_answer:
                correct_count += 1
            else:
                wrong_items.append({
                    "question": qa_pair.get("question"),
                    "prediction": pred,
                    "correct_answer_text": answer,
                    "options": qa_pair.get("options"),
                    "expected_index": answer_index,
                    "original_model_answer": model_answer
                })

            total_valid_data_num += 1

    accuracy = correct_count / total_valid_data_num if total_valid_data_num > 0 else 0
    print(f"Overall Correct: {correct_count}/{total_valid_data_num}, Accuracy: {accuracy:.2%}\n")

    if wrong_items:
        print("--- Incorrectly Answered Items ---")
        for i, wrong_item in enumerate(wrong_items[:10]): # Print first 10 wrong items as an example
            print(f"\nWrong Item {i+1}:")
            print(f"  Question: {wrong_item.get('question')}")
            print(f"  Options: {wrong_item.get('options')}")
            print(f"  Prediction: '{wrong_item.get('prediction')}'")
            print(f"  Correct Answer Text: '{wrong_item.get('correct_answer_text')}'")
            print(f"  Expected Index: {wrong_item.get('expected_index')}")
            print(f"  Original Model Output: '{wrong_item.get('original_model_answer')}'")
        if len(wrong_items) > 10:
            print(f"\n... and {len(wrong_items) - 10} more incorrect items.")

if __name__ == "__main__":
    main()