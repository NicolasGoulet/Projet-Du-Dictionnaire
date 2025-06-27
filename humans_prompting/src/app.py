import os
import pandas as pd
import csv
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
# Use an environment variable for the secret key in production; default for development.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key_for_dev')

# Set the base directory (one level up from src)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_FILE = os.path.join(BASE_DIR, "data", "selected_prompts.csv")

# Load the CSV data into a list of dictionaries.
data = pd.read_csv(DATA_FILE)
trials = data.to_dict(orient='records')

def get_options(text):
    """
    Splits the choices text by "Modified word:" and returns a list of option dictionaries.
    Each option is a dict with keys 'vocable' and 'definition'. If "Definition:" is present,
    the text is split into two parts.
    """
    parts = text.split("Modified word:")
    options = []
    for part in parts:
        part = part.strip()
        if part:
            if "Definition:" in part:
                vocable, definition = part.split("Definition:", 1)
                vocable = "Modified word: " + vocable.strip()
                definition = "Definition: " + definition.strip()
            else:
                vocable = "Modified word: " + part.strip()
                definition = ""
            options.append({"vocable": vocable, "definition": definition})
    return options

@app.route('/')
def index():
    return redirect(url_for('welcome'))

# Welcome page: asks for participant's name.
@app.route('/welcome', methods=['GET', 'POST'])
def welcome():
    if request.method == 'POST':
        participant_name = request.form.get('participant_name', '').strip()
        if participant_name == '':
            return render_template('welcome.html', error="Please enter your name.")
        # Save the participant's name in session.
        session['participant_name'] = participant_name
        # Create a safe filename using the participant's name.
        safe_name = "".join(c for c in participant_name if c.isalnum() or c in (' ', '_')).rstrip().replace(" ", "_")
        results_file = os.path.join(BASE_DIR, "results", f"{safe_name}_results.csv")
        session['results_file'] = results_file
        # Initialize the participant's results file if it does not exist.
        if not os.path.exists(results_file):
            with open(results_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['trial_id', 'word', 'selected_answer', 'participant_name'])
        return redirect(url_for('instructions'))
    return render_template('welcome.html')

# Instructions page.
@app.route('/instructions')
def instructions():
    return render_template('instructions.html')

# Trial route: shows each trial (row from the CSV).
@app.route('/trial/<int:trial_id>', methods=['GET', 'POST'])
def trial(trial_id):
    if trial_id >= len(trials):
        return redirect(url_for('thankyou'))

    trial_data = trials[trial_id]
    # Process the choices text into a list of option dictionaries.
    options = get_options(trial_data['choices_1'])

    if request.method == 'POST':
        selected_answer = request.form.get('answer')
        results_file = session.get('results_file')
        participant_name = session.get('participant_name')
        # Save the trial result to the participant-specific results CSV.
        with open(results_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([trial_id, trial_data['word'], selected_answer, participant_name])
        return redirect(url_for('trial', trial_id=trial_id+1))

    return render_template('trial.html', trial=trial_data, trial_id=trial_id, total_trials=len(trials), options=options)

# Thank-you page.
@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

if __name__ == '__main__':
    app.run(debug=True)
