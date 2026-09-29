from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import zipfile
import urllib.request
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient
from pymongo.collection import ReturnDocument
from config import settings


CHROME_PARENT_DIR = "/tmp/.local-chrome"         # Writable directory
CHROME_FOLDER_PATH = f"{CHROME_PARENT_DIR}/chrome"
CHROME_BINARY_PATH = f"{CHROME_FOLDER_PATH}/chrome"
CHROME_ZIP_PATH = "/tmp/chrome.zip"
CHROMIUM_URL = "https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/1140000/chrome-linux.zip"


def download_chrome_if_missing():
    if not os.path.exists(CHROME_BINARY_PATH):
        print("Downloading headless Chrome...")
        os.makedirs(CHROME_PARENT_DIR, exist_ok=True)
        urllib.request.urlretrieve(CHROMIUM_URL, CHROME_ZIP_PATH)

        with zipfile.ZipFile(CHROME_ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(CHROME_PARENT_DIR)

        os.rename(f"{CHROME_PARENT_DIR}/chrome-linux", CHROME_FOLDER_PATH)

        # Make Chrome executable
        os.chmod(CHROME_BINARY_PATH, 0o755)


def setup_driver():
    try:
        import platform
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')

        if platform.system() == 'Linux':
            # Production / Render: download Chromium if missing
            download_chrome_if_missing()
            chrome_options.binary_location = CHROME_BINARY_PATH

        # On Windows/Mac: ChromeDriverManager finds the system Chrome automatically
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        return driver
    except Exception as e:
        print(f"Error setting up Chrome WebDriver: {e}")
        raise

source_text=""

def find_and_add_blank(driver, blank_number):
    try:
        # Wait for the editor iframe to be present
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cke_wysiwyg_frame"))
        )
        
        # Switch to the iframe
        driver.switch_to.frame(iframe)
        
        # Find the editable body element
        editor_body = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cke_editable"))
        )
        
        # Get the text content
        content = editor_body.text
        
        # Find the position of the text
        target_text = f"Blank {blank_number}: Enter your code here"
        if target_text in content:
            # Click at the start of the text using a more robust approach
            script = """
            function findTextAndSetCursor(element, searchText) {
                const walker = document.createTreeWalker(
                    element,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );
                
                let node;
                let offset = 0;
                
                while (node = walker.nextNode()) {
                    const index = node.textContent.indexOf(searchText);
                    if (index !== -1) {
                        const range = document.createRange();
                        range.setStart(node, index);
                        range.collapse(true);
                        
                        const selection = window.getSelection();
                        selection.removeAllRanges();
                        selection.addRange(range);
                        return true;
                    }
                    offset += node.textContent.length;
                }
                return false;
            }
            
            return findTextAndSetCursor(arguments[0], arguments[1]);
            """
            
            success = driver.execute_script(script, editor_body, target_text)
            if not success:
                 print(f"Could not position cursor at Blank {blank_number}")
                 driver.switch_to.default_content()
                 return False
        else:
             print(f"Could not find Blank {blank_number} in the editor")
             driver.switch_to.default_content()
             return False
        
        # Switch back to default content
        driver.switch_to.default_content()
        
        # Now click the Add Answer Box link using JavaScript
        try:
            # Wait for the element to be present
            add_answer_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "lnkAddAnswerBox"))
            )
            
            # Scroll the element into view
            driver.execute_script("arguments[0].scrollIntoView(true);", add_answer_box)
            time.sleep(1)
            
            # Click using JavaScript
            driver.execute_script("arguments[0].click();", add_answer_box)
            time.sleep(2)
            
            # Wait for the modal to appear (wait for the modal title or unique element)
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'modal-content')]//h4[contains(text(), 'Add Answer Box')]"))
            )
            
            # Select answer size from dropdown
            try:
                # Click the answer size dropdown
                answer_size = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "answerSize"))
                )
                answer_size.click()
                time.sleep(1)
                
                # Select option with value="2"
                size_option = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//select[@id='answerSize']/option[@value='2']"))
                )
                size_option.click()
                time.sleep(1)
            except Exception as e:
                print(f"Error while selecting answer size: {e}")
                return False
            
            # Wait for the Save button inside the modal and click it
            try:
                save_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".modal-content .btn.btn-primary-imocha"))
                )
                save_button.click()
                time.sleep(2)
                return True
            except Exception as e:
                print(f"Error while trying to find and click Save button in modal: {e}")
                print("Page source at time of error:")
                print(driver.page_source)
                return False
            
        except Exception as e:
            print(f"Error while trying to click Add Answer Box link: {e}")
            return False
        
    except Exception as e:
        print(f"Error in find_and_add_blank: {e}")
        # Make sure we switch back to default content even if there's an error
        try:
            driver.switch_to.default_content()
        except:
            pass
        return False

def clean_and_format(input_str: str):
    cleaned = ''
    for char in input_str:
        ascii_val = ord(char)
        # Keep letters (A-Z, a-z), digits (0-9), and space (ASCII 32)
        if (65 <= ascii_val <= 90) or (97 <= ascii_val <= 122) or (48 <= ascii_val <= 57) or ascii_val == 32:
            cleaned += char
        else:
            cleaned += ' '  # Replace special characters with space
 
    # Split into words
    words = cleaned.strip().split()
    return ', '.join(words), len(words)

def style_question(source, num_blanks=5):
    target_substring = 'A few lines in the Sample Script are missing (Enter your code here).'

    # Find the index where the target substring ends
    split_index = source.find(target_substring)

    # Split the string into two parts
    left_source = source[:split_index]
    right_source = source[split_index:]

    left_table = """
    <style type="text/css">
    .sqlTable {
        border: none;
        width: 100%;
    }
    .sqlTable thead tr th {
        background: #f3f6fc;
        border-bottom: 1px solid #d8e3fb;
        text-align: center;
        padding: 7px;
        line-height: 1.3;
    }
    .sqlTable tbody tr td {
        border-bottom: 1px solid #d8e3fb;
        text-align: center;
        padding: 7px;
        line-height: 1.3;
    }
    .sqlTable tr:nth-child(odd) {
        background: #f6fcff;
        border-bottom: 1px solid #d8e3fb;
    }
    </style>
    <section style="float:left; padding: 10px; display: block;">
    <div style="width:50%; float:left;">
    """

    mid_table="""
        </div>

        <div style="width:46%; float:right; padding: 15px;">
    """

    right_table="""
        </div>
        </section>
    """
    result_source=left_table

    result_source+=left_source

    result_source+=mid_table

    result_source+=right_source

    result_source+=right_table

    result_source=style_blank(result_source, num_blanks)


    # Remove the specified substrings
    for i in range(1, num_blanks + 1):
        substring1 = f'Blank {i}: Enter your code here<br />'
        substring2= f'At Blank {i}:'
                    
        result_source = result_source.replace(substring1, f'<br/>')
        result_source = result_source.replace(substring2, f'<strong>At Blank {i}: </strong>')
                
    substring3= f'Complete the code as per the given instructions:'
    substring4= f'A few lines in the Sample Script are missing (Enter your code here).'

    substring5=f'You need to complete the code as per the given instructions.'

    substring6= f'Sample Script:'

    result_source = result_source.replace(substring3, f'<strong>Complete the code as per the given instructions:</strong>')

    result_source= result_source.replace(substring4, f'<strong>A few lines in the Sample Script are missing (Enter your code here).</strong>')
     
    result_source= result_source.replace(substring5, f'<strong>You need to complete the code as per the given instructions.</strong>')

    result_source= result_source.replace(substring6, f'<strong>Sample Script:</strong>')

    return result_source

def style_blank(source, num_blanks=5):
    target_substring1= f'cols="50"'

    updating_string1= f'cols="40"'

    # Replace target_substring1 with updating_string1
    source = source.replace(target_substring1, updating_string1)

    for i in range(1, num_blanks + 1):
        target_substring2= f'placeholder="Answer{i}" rows="5"'

        updating_string2= f'placeholder="Blank {i}: Enter your code here" rows="1" style=" border: 1px solid #32ece4; box-shadow: 0 0 10px #d6eceb; padding: 5px 7px;"'
        
        # Replace target_substring2 with updating_string2
        source = source.replace(target_substring2, updating_string2)
    return source

def put_source_text(driver, resultingsource):
    try:
        # Find the source editor element
        editor_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cke_source"))
        )
        print("Found editor element")
        
        # Clear the existing content
        driver.execute_script("arguments[0].value = '';", editor_element)
        print("Cleared existing content")
        
        # Set the new content
        driver.execute_script("arguments[0].value = arguments[1];", editor_element, resultingsource)
        
        # Trigger change event to ensure CKEditor updates
        driver.execute_script("""
            var element = arguments[0];
            var event = new Event('change', { bubbles: true });
            element.dispatchEvent(event);
        """, editor_element)
        print("Triggered change event")
        
        return True
        
    except Exception as e:
        print(f"Error while updating source text: {e}")
        return False

def extract_source_text(driver, num_blanks=5):
    try:
        # Now find the editable element
        editor_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "cke_source"))
                        )
        # Get the text content
        source_text = editor_element.get_attribute('value')
        if source_text:
                resulting_source=style_question(source_text, num_blanks)
                
                # Update the editor with styled content
                if put_source_text(driver, resulting_source):
                    print("Source text updated successfully")
                    driver.switch_to.default_content()
                    return True
                else:
                    print("Failed to update source text")
                    driver.switch_to.default_content()
                    return False
        else:
            print("No content found in editor")
            driver.switch_to.default_content()
            return False
                                    
    except Exception as e:
        print(f"Error while accessing editor: {e}")
        # Make sure we switch back to default content
        try:
            driver.switch_to.default_content()
        except:
            pass
        return False

def enter_text_in_editor(driver, text, num_blanks=5):
    try:
        # Wait for the editor iframe to be present
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cke_wysiwyg_frame"))
        )

        # Switch to the iframe
        driver.switch_to.frame(iframe)

        # Find the editable body element
        editor_body = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cke_editable"))
        )

        # Clear any existing text
        editor_body.clear()

        # Enter the text ONLY ONCE
        editor_body.send_keys(text)

        # Switch back to default content
        driver.switch_to.default_content()

        # Wait for the text to be entered
        time.sleep(2)

        # Add blanks one by one
        for i in range(1, num_blanks + 1):
            # Add the blank
            if not find_and_add_blank(driver, i):
                print(f"Failed to add blank {i}. Aborting.")
                return False # Stop if adding a blank fails

        return True

    except Exception as e:
        print(f"Error while entering text in editor: {e}")
        try:
            driver.switch_to.default_content()
        except:
            pass
        return False

def add_all_answer_sets(driver, answers, overall_marks=10, num_blanks=5):
    """
    Gets structured answer input from the user and adds all alternative answer sets for each blank.
    Returns the original answer text for explanation.
    """
    full_credit = max(1, overall_marks // num_blanks)
    partial_credit = full_credit // 2
    answer_input = {} # Dictionary to store answers by blank number
    current_blank = None
    original_answer_text = answers # Store the original text

    # Parse the input
    lines = answers.splitlines()
    for line in lines:
        line = line.strip()
        if line.lower().startswith("blank ") and line.endswith(":"):
            try:
                blank_number = int(line.split()[1][:-1]) # Extract number from "Blank X:"
                current_blank = blank_number
                answer_input[current_blank] = [] # Initialize list for this blank's answers
            except (ValueError, IndexError):
                print(f"Warning: Could not parse blank number from line: {line}")
                current_blank = None # Reset if parsing fails
        elif current_blank is not None and line:
            # Check if line starts with a number followed by a dot and space/end
            parts = line.split('. ', 1)
            if len(parts) == 2 and parts[0].isdigit():
                alternative_text = parts[1].strip()
                answer_input[current_blank].append(alternative_text)
            else:
                 print(f"Warning: Skipping unparseable line for Blank {current_blank}: {line}")

    # Now, iterate through blanks and add their answer sets
    for i in range(1, num_blanks + 1):
        if i in answer_input:
            print(f"\nProcessing Answer Sets for Blank {i}")
            alternatives = answer_input[i]
            if not alternatives:
                print(f"No alternative answers found for Blank {i}.")
                continue

            # --- First Pass: Add all alternatives for full_credit marks ---
            print(f"\n  Adding Answer Sets for Blank {i} with {full_credit} points")
            for j, answer_alt_text in enumerate(alternatives):
                print(f"   Processing Alternative {j+1} for {full_credit} points")
                try:
                    # Clean and format the answer text
                    cleaned_answer, answer_length = clean_and_format(answer_alt_text)
                    keyword_count_value = answer_length # Keyword count for full credit marks
                    points_value = full_credit # Points for this pass

                    # Find the specific blank's container div
                    blank_container = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, f"Answer{i}"))
                    )

                    # Scroll the container into view
                    driver.execute_script("arguments[0].scrollIntoView(true);", blank_container)
                    time.sleep(1)

                    # Find the plus icon within this specific blank container
                    plus_icon = WebDriverWait(blank_container, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".im-icon.icon-im-plus"))
                    )

                    # Try to click using JavaScript
                    try:
                        driver.execute_script("arguments[0].click();", plus_icon)
                    except:
                        # If JavaScript click fails, try regular click
                        plus_icon.click()

                    time.sleep(2) # Wait for modal to appear

                    # Wait for the Add Answer Set modal to be visible
                    WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'modal-content')]//h4[contains(text(), 'Add Answer Set')]"))
                    )

                    # Enter answer text
                    set_answer = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "setAnswer"))
                    )
                    set_answer.clear()
                    set_answer.send_keys(cleaned_answer)
                    time.sleep(1)

                    # Click the radio button
                    radio_label = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[title="checks if the candidate answer includes keywords present in the answer set"]'))
                    )
                    radio_input = radio_label.find_element(By.XPATH, ".//input[@type='radio']")
                    driver.execute_script("arguments[0].click();", radio_input)
                    time.sleep(1)

                    # Set keyword count
                    set_keyword_count = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "setKeywordCount"))
                    )
                    set_keyword_count.clear()
                    set_keyword_count.send_keys(str(keyword_count_value))
                    time.sleep(1)

                    # Set points
                    set_points = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "setPoints"))
                    )
                    set_points.clear()
                    set_points.send_keys(str(points_value))
                    time.sleep(1)

                    # Save the answer set modal
                    add_answer_set_div = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "addAnswerSet"))
                    )
                    save_btn = add_answer_set_div.find_element(By.CSS_SELECTOR, ".btn.btn-primary-imocha")
                    driver.execute_script("arguments[0].click();", save_btn)
                    time.sleep(4) # Wait for modal to close

                    print(f"Successfully added Answer Set for Alternative {j+1} (Points: {points_value}, Keyword Count: {keyword_count_value})")

                except Exception as e:
                    print(f"Error while adding Answer Set for Alternative {j+1} (Points: {points_value}, Keyword Count: {keyword_count_value}) for Blank {i}: {e}")
                    # Attempt to close the modal if it's open to avoid blocking subsequent steps
                    try:
                        cancel_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, ".modal-content .btn.btn-default"))
                        )
                        driver.execute_script("arguments[0].click();", cancel_btn)
                        time.sleep(1)
                    except:
                        pass # Ignore if cancel button not found or clickable

            # --- Second Pass: Add all alternatives for partial_credit marks ---
            if partial_credit == 0:
                print(f"\n  Skipping partial credit pass for Blank {i} (full_credit={full_credit}, partial would be 0)")
                try:
                    if save_content(driver):
                        print(f"Successfully saved all answer sets for Blank {i}")
                except Exception as e:
                    print(f"Error while saving Answer Set for Blank {i}: {e}")
                continue

            print(f"\n  Adding Answer Sets for Blank {i} with {partial_credit} point")
            for j, answer_alt_text in enumerate(alternatives):
                print(f"   Processing Alternative {j+1} for {partial_credit} point")
                try:
                    # Clean and format the answer text
                    cleaned_answer, answer_length = clean_and_format(answer_alt_text)

                    if answer_length == 1:
                        continue

                    keyword_count_value = (answer_length // 2) if answer_length % 2 == 0 else (answer_length // 2) + 1
                    points_value = partial_credit # Points for this pass

                    # Find the specific blank's container div
                    blank_container = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, f"Answer{i}"))
                    )

                    # Scroll the container into view
                    driver.execute_script("arguments[0].scrollIntoView(true);", blank_container)
                    time.sleep(1)

                    # Find the plus icon within this specific blank container
                    plus_icon = WebDriverWait(blank_container, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".im-icon.icon-im-plus"))
                    )

                    # Try to click using JavaScript
                    try:
                        driver.execute_script("arguments[0].click();", plus_icon)
                    except:
                        # If JavaScript click fails, try regular click
                        plus_icon.click()

                    time.sleep(2) # Wait for modal to appear

                    # Wait for the Add Answer Set modal to be visible
                    WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'modal-content')]//h4[contains(text(), 'Add Answer Set')]"))
                    )

                    # Enter answer text
                    set_answer = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "setAnswer"))
                    )
                    set_answer.clear()
                    set_answer.send_keys(cleaned_answer)
                    time.sleep(1)

                    # Click the radio button
                    radio_label = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[title="checks if the candidate answer includes keywords present in the answer set"]'))
                    )
                    radio_input = radio_label.find_element(By.XPATH, ".//input[@type='radio']")
                    driver.execute_script("arguments[0].click();", radio_input)
                    time.sleep(1)

                    # Set keyword count
                    set_keyword_count = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "setKeywordCount"))
                    )
                    set_keyword_count.clear()
                    set_keyword_count.send_keys(str(keyword_count_value))
                    time.sleep(1)

                    # Set points
                    set_points = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "setPoints"))
                    )
                    set_points.clear()
                    set_points.send_keys(str(points_value))
                    time.sleep(1)

                    # Save the answer set modal
                    add_answer_set_div = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "addAnswerSet"))
                    )
                    save_btn = add_answer_set_div.find_element(By.CSS_SELECTOR, ".btn.btn-primary-imocha")
                    driver.execute_script("arguments[0].click();", save_btn)
                    time.sleep(4) # Wait for modal to close

                    print(f"   Successfully added Answer Set for Alternative {j+1} (Points: {points_value}, Keyword Count: {keyword_count_value})")

                except Exception as e:
                    print(f"Error while adding Answer Set for Alternative {j+1} (Points: {points_value}, Keyword Count: {keyword_count_value}) for Blank {i}: {e}")
                    # Attempt to close the modal if it's open to avoid blocking subsequent steps
                    try:
                        cancel_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, ".modal-content .btn.btn-default"))
                        )
                        driver.execute_script("arguments[0].click();", cancel_btn)
                        time.sleep(1)
                    except:
                        pass # Ignore if cancel button not found or clickable
                    
            try:
                if save_content(driver):
                    print(f"Successfully saved all answer sets for Blank {i}")
            except Exception as e:
                print(f"Error while saving Answer Set for for Blank {i}: {e}")

    return original_answer_text

def login_to_website(driver, url, username, password, dropdown_text, source_text, num_blanks=5):
    try:
        driver.get(url)
        time.sleep(3)

        # Step 1: Email
        try:
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "EmailId"))
            )
            email_field.clear()
            email_field.send_keys(username)
            continue_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "frmSubmitBtn"))
            )
            continue_button.click()
            time.sleep(3)
        except Exception as e:
            print(f"[login] Step 1 (email): {e}")
            return False, f"Could not find email field or continue button: {e}"

        # Step 2: Password
        try:
            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "Password"))
            )
            password_field.clear()
            password_field.send_keys(password)
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
            )
            login_button.click()
            time.sleep(5)
        except Exception as e:
            print(f"[login] Step 2 (password): {e}")
            return False, f"Could not find password field or login button: {e}"

        # Step 3: Verify login succeeded
        current_url = driver.current_url.lower()
        if "login" in current_url or "signin" in current_url:
            print("[login] Still on login page — wrong credentials?")
            return False, "Login failed: wrong username or password"

        time.sleep(2)

        # Step 4: Navigate to My Questions
        try:
            my_questions_url = (
                f"{settings.imocha_base_url}/MyQuestions/SharedQuestions"
                if "rtu" in username.lower()
                else f"{settings.imocha_base_url}/MyQuestions/Index"
            )
            driver.get(my_questions_url)
            time.sleep(2)
            if "myquestions" not in driver.current_url.lower():
                print("[login] Could not reach My Questions page")
                return False, "Could not navigate to My Questions page"
        except Exception as e:
            print(f"[login] Step 4 (navigate): {e}")
            return False, f"Error navigating to My Questions: {e}"

        # Step 5: Add Question button
        try:
            add_question_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "add-que-btn"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", add_question_btn)
            time.sleep(1)
            add_question_btn.click()
            time.sleep(3)
        except Exception as e:
            print(f"[login] Step 5 (add question btn): {e}")
            return False, f"Could not click Add Question button: {e}"

        # Step 6: Logic Box type
        try:
            add_coding_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, ".//*[@data-trackuser='my questions: Logic Box']"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", add_coding_element)
            time.sleep(1)
            add_coding_element.click()
            time.sleep(30)
        except Exception as e:
            print(f"[login] Step 6 (Logic Box): {e}")
            return False, f"Could not click Logic Box question type: {e}"

        # Step 7: Question bank dropdown
        try:
            select2_container = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.ID, "select2-ddlQB-container"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", select2_container)
            time.sleep(25)
            select2_container.click()
            time.sleep(20)
        except Exception as e:
            print(f"[login] Step 7 (question bank dropdown): {e}")
            return False, f"Could not open question bank dropdown: {e}"

        # Step 8: Select the question bank
        try:
            dropdown_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//li[contains(text(), '{dropdown_text}')]"))
            )
            dropdown_option.click()
            time.sleep(2)
        except Exception as e:
            print(f"[login] Step 8 (select bank '{dropdown_text}'): {e}")
            return False, f"Could not find question bank '{dropdown_text}' in dropdown: {e}"

        # Step 9: Enter question text and add blanks
        if enter_text_in_editor(driver, source_text, num_blanks):
            print("[login] Successfully entered text and added blanks.")
            return True, None
        else:
            print("[login] Failed to enter text in editor or add blanks.")
            return False, "Failed to enter question text or add blank boxes in the editor"

    except Exception as e:
        print(f"[login] Unexpected error: {e}")
        return False, f"Unexpected error during login: {e}"

def add_question(driver, question, num_blanks=5):
    try:
        # Enter text in the editor and add blanks
        if enter_text_in_editor(driver, question, num_blanks):
            print("Successfully entered question and added blanks.")
            return True
        else:
            print("Failed to enter question in editor.")
            return False
    except Exception as e:
        print(f"Error while adding question: {e}")
        return False

def style_source(driver, num_blanks=5):
    try:
        # Wait for any existing modals to be closed
        try:
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "modal-body"))
            )
        except:
            pass  # Ignore if no modal is present

        # Find the source button
        btn_source = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "cke_53_label"))
        )

        # Scroll the button into view
        driver.execute_script("arguments[0].scrollIntoView(true);", btn_source)
        time.sleep(1)  # Give time for scroll to complete

        # Try to click using JavaScript first
        try:
            driver.execute_script("arguments[0].click();", btn_source)
        except:
            # If JavaScript click fails, try regular click
            btn_source.click()

        print("Clicked source button")
        time.sleep(3)

        # Extract and style source text
        if extract_source_text(driver, num_blanks):
            print("Source text styled successfully")
            return True
        else:
            print("Failed to style source text")
            return False
    except Exception as e:
        print(f"Error while styling source: {e}")
        return False

def save_content(driver):
    try:
        # Wait for any existing modals to be closed
        try:
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "modal-body"))
            )
        except:
            pass  # Ignore if no modal is present

        # Find the save button
        btn_save = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "btnSave"))
        )

        # Scroll the button into view
        driver.execute_script("arguments[0].scrollIntoView(true);", btn_save)
        time.sleep(1)  # Give time for scroll to complete

        # Try to click using JavaScript first
        try:
            driver.execute_script("arguments[0].click();", btn_save)
        except:
            # If JavaScript click fails, try regular click
            btn_save.click()

        print("Clicked save button")
        time.sleep(2)
        try:
          
          confirmation_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "btnProofReadingConfirmYes"))
          )
          confirmation_button.click()
          print("Clicked confirmation button.")
          time.sleep(2)
          return True
        except Exception:
          print(f"Confirmation button not found. Final Question Saved.")
          return True
    except Exception as e:
        print(f"Error while saving content: {e}")
        return False

def set_difficulty_level(driver, difficulty):
    try:
        # Wait for any existing modals to be closed
        try:
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "modal-body"))
            )
        except:
            pass  # Ignore if no modal is present

        # Find the difficulty level dropdown
        difficulty_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "DifficLevel"))
        )

        # Scroll the dropdown into view
        driver.execute_script("arguments[0].scrollIntoView(true);", difficulty_dropdown)
        time.sleep(1)  # Give time for scroll to complete

        # Try to click using JavaScript first
        try:
            driver.execute_script("arguments[0].click();", difficulty_dropdown)
        except:
            # If JavaScript click fails, try regular click
            difficulty_dropdown.click()

        time.sleep(1)

        # Select the appropriate difficulty level using JavaScript
        script = f"""
        var select = document.getElementById('DifficLevel');
        select.value = '{difficulty}';
        var event = new Event('change', {{ bubbles: true }});
        select.dispatchEvent(event);
        """
        driver.execute_script(script)
        time.sleep(1)
        return True
    except Exception as e:
        print(f"Error while setting difficulty level: {e}")
        return False

def add_answer_explanation(driver, explanation_text):
    try:
        # Find the explanation textarea
        explanation_textarea = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "txtAnswerExplanation"))
        )
        
        # Clear any existing text
        explanation_textarea.clear()
        
        # Add the explanation text
        explanation_textarea.send_keys(explanation_text)
        time.sleep(1)
        return True
    except Exception as e:
        print(f"Error while adding answer explanation: {e}")
        return False

# Function to increment the global counter in MongoDB
def increment_global_counter():
    if not settings.mongo_url:
        raise RuntimeError('MONGO_URL environment variable not set')

    client = MongoClient(settings.mongo_url)
    try:
        counters = client[settings.mongo_database][settings.mongo_collection]
        counters.find_one_and_update(
            {"_id": settings.counter_id},
            {"$inc": {"counter": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        print("Global counter incremented successfully")
    finally:
        client.close()

def main_to_execute(username, password, question, answer_sets, difficulty, author, topic, question_bank, overall_marks=10, num_blanks=5):
    driver = None

    try:
        driver = setup_driver()

        login_ok, login_reason = login_to_website(
            driver, settings.imocha_base_url, username, password, question_bank, question, num_blanks
        )
        if not login_ok:
            return False, login_reason

        explanation_text = add_all_answer_sets(driver, answer_sets, overall_marks, num_blanks)
        if not explanation_text:
            return False, "Failed to add answer sets (check answer format)"

        if not save_content(driver):
            return False, "Failed to save content after adding answer sets"

        if not style_source(driver, num_blanks):
            return False, "Failed to style question source HTML"

        if not set_difficulty_level(driver, difficulty):
            return False, "Failed to set difficulty level"

        if not add_author(driver, author):
            return False, "Failed to add author"

        if not add_topic(driver, topic):
            return False, "Failed to add topic"

        if not add_answer_explanation(driver, explanation_text):
            return False, "Failed to add answer explanation"

        if not final_save(driver):
            return False, "Failed to perform final save"

        increment_global_counter()
        return True, None

    except Exception as e:
        print(f"An error occurred: {e}")
        return False, str(e)

    finally:
        if driver:
            driver.quit()

def add_author(driver, author):
    try:
        # Find the author textarea
        author_textarea = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "txtAuthor"))
        )
        
        # Clear any existing text
        author_textarea.clear()
        
        # Add the author name
        author_textarea.send_keys(author)
        time.sleep(1)
        return True
    except Exception as e:
        print(f"Error while adding author: {e}")
        return False

def add_topic(driver, topic):
    try:
        # Find the tag textarea
        tag_textarea = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "txtTag"))
        )
        
        # Clear any existing text
        tag_textarea.clear()
        
        # Add the topic
        tag_textarea.send_keys(topic)
        time.sleep(1)
        return True
    except Exception as e:
        print(f"Error while adding topic: {e}")
        return False

def final_save(driver):
    if not settings.imocha_write_enabled:
        print("iMocha write operations are disabled.")
        return False
    try:
        # Click save button one final time
        final_save_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btnSave"))
        )
        final_save_btn.click()
        print("Clicked final save button")
        time.sleep(2)
        try:
          
          confirmation_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "btnProofReadingConfirmYes"))
          )
          confirmation_button.click()
          print("Clicked confirmation button.")
          time.sleep(2)
          return True
        except Exception:
          print(f"Confirmation button not found. Final Question Saved.")
          return True
    except Exception as e:
        print(f"Error while performing final save: {e}")
        return False
