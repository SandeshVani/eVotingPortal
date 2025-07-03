# --- Import necessary modules from Flask and standard libraries ---

from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from datetime import datetime, timedelta

# Importing the database manager
from DBManager import DatabaseManager

# --- Initializing the Flask Application ---
app = Flask(__name__)
# A secret key is required for session management (to keep users logged in)
app.secret_key = 'a_very_secret_and_hard_to_guess_key'

# --- Database Setup ---
# Create a single instance of the database manager for the whole app.
db = DatabaseManager(user="root", password="Qawsedrftg@1", host="localhost", database="eVotingMpDb")

# --- Admin Credentials (from your original code) ---
ADMIN_USERNAME = "admin@"
ADMIN_PASSWORD = "pass123"

# --- Decorators for Access Control ---
# Decorators are a way to add functionality to an existing function.
# We use them here to check if a user is logged in and has the correct role.

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If 'user_type' is not in the session or is not 'admin', they are not allowed.
        if session.get('user_type') != 'admin':
            flash("You need to be logged in as an admin to view this page.", "danger")
            return redirect(url_for('login', user_type='admin'))
        # If they are an admin, run the original function (e.g., admin_dashboard).
        return f(*args, **kwargs)
    return decorated_function

def voter_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if the user is a logged-in voter.
        if session.get('user_type') != 'voter':
            flash("You need to be logged in as a voter to view this page.", "danger")
            return redirect(url_for('login', user_type='voter'))
        # If they are, run the original function.
        return f(*args, **kwargs)
    return decorated_function

# --- Main and Authentication Routes ---

@app.route('/')
def home():
    """Renders the main landing page."""
    return render_template('home.html')

# Login 

@app.route('/login/<user_type>', methods=['GET', 'POST'])
def login(user_type):
    """Handles login for both Admins and Voters with corrected attempt logic for BOTH."""
    
    # --- Check for Admin Block before processing the request ---
    if user_type == 'admin' and 'admin_blocked_until' in session:
        block_time = session.get('admin_blocked_until')
        if datetime.now() < block_time:
            flash(f"Admin login is blocked. Please try again after {block_time.strftime('%I:%M %p')}.", 'warning')
            return render_template('login.html', user_type=user_type, admin_is_blocked=True)
        else:
            # If the block time has passed, clear it from the session
            session.pop('admin_blocked_until', None)

    if request.method == 'GET':
        return render_template('login.html', user_type=user_type)

    # --- POST Request Logic ---
    username = request.form['username']
    password = request.form['password']

    # --- Admin Login Logic with Attempt Tracking ---
    if user_type == 'admin':
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            # On success, clear any admin attempt tracking from the session
            session.pop('admin_attempts', None)
            session.pop('admin_blocked_until', None)
            session['user_type'] = 'admin'
            session['username'] = username
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            # On failure, get current attempts from session, or 0 if not present
            attempts = session.get('admin_attempts', 0) + 1
            session['admin_attempts'] = attempts

            if attempts >= 3:
                # Block the admin for 2 minutes
                block_time = datetime.now() + timedelta(minutes=2)
                session['admin_blocked_until'] = block_time
                session.pop('admin_attempts', None) # Clear attempts after blocking
                flash('Incorrect credentials. Admin login has been blocked for 2 minutes.', 'danger')
            else:
                attempts_left = 3 - attempts
                flash(f'Invalid admin credentials. You have {attempts_left} attempt(s) left.', 'danger')
            
            return redirect(url_for('login', user_type='admin'))

    # --- Voter Login Logic (this part is already correct) ---
    elif user_type == 'voter':
        voter_id = username.upper().strip()
        voter_data = db.fetch("SELECT * FROM voters WHERE VoterID = %s", (voter_id,))
        if not voter_data:
            flash('Voter ID not registered.', 'danger')
            return redirect(url_for('login', user_type='voter'))
        voter = voter_data[0]
        if voter['BlockUntil'] and datetime.now() < voter['BlockUntil']:
            flash(f"Account is blocked. Please try again after {voter['BlockUntil'].strftime('%I:%M %p')}.", 'warning')
            return redirect(url_for('login', user_type='voter'))
        if password == voter['Password']:
            db.update("UPDATE voters SET FailedAttempts = 0, BlockUntil = NULL WHERE VoterID = %s", (voter_id,))
            session['user_type'] = 'voter'
            session['voter_id'] = voter_id
            flash('Login successful!', 'success')
            return redirect(url_for('voter_dashboard'))
        else:
            db.update("UPDATE voters SET FailedAttempts = FailedAttempts + 1 WHERE VoterID = %s", (voter_id,))
            updated_voter_data = db.fetch("SELECT FailedAttempts FROM voters WHERE VoterID = %s", (voter_id,))
            current_attempts = updated_voter_data[0]['FailedAttempts']
            if current_attempts >= 3:
                block_time = datetime.now() + timedelta(minutes=2)
                db.update("UPDATE voters SET BlockUntil = %s WHERE VoterID = %s", (block_time, voter_id))
                flash('Incorrect password. Your account has been blocked for 2 minutes.', 'danger')
            else:
                attempts_left = 3 - current_attempts
                flash(f'Incorrect password. You have {attempts_left} attempt(s) left.', 'danger')
            return redirect(url_for('login', user_type='voter'))

    return redirect(url_for('home'))



@app.route('/logout')
def logout():
    """Clears the session to log the user out."""
    session.clear()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('home'))


# --- Admin Routes ---

@app.route('/admin/dashboard')
@admin_required # This route is protected by our decorator
def admin_dashboard():
    """The main dashboard for the admin, showing all campaigns."""
    campaigns = db.fetch("SELECT * FROM campaigns ORDER BY StartDate DESC")
    return render_template('admin_dashboard.html', campaigns=campaigns or [])

@app.route('/admin/campaign/new', methods=['GET', 'POST'])
@admin_required
def create_campaign():
    """Handles the creation of a new campaign."""
    if request.method == 'POST':
        # Logic to process the form data and insert into the database
        cid = request.form['cid']
        name = request.form['name']
        const = request.form['constituency']
        start = request.form['start_date']
        end = request.form['end_date']
        
        s_dt = datetime.strptime(start, "%Y-%m-%dT%H:%M")
        e_dt = datetime.strptime(end, "%Y-%m-%dT%H:%M")
        status = "Active" if s_dt <= datetime.now() <= e_dt else "Upcoming"

        query = "INSERT INTO campaigns (CampaignID, CampaignName, ConstituencyName, StartDate, EndDate, Status) VALUES (%s, %s, %s, %s, %s, %s)"
        if db.update(query, (cid, name, const, s_dt, e_dt, status)):
            flash('Campaign created successfully!', 'success')
        else:
            flash('Failed to create campaign. The ID might already exist.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    # On a GET request, just show the form.
    return render_template('campaign_form.html', form_action='Create', campaign={})

@app.route('/admin/campaign/edit/<campaign_id>', methods=['GET', 'POST'])
@admin_required
def update_campaign(campaign_id):
    """Handles editing an existing campaign."""
    if request.method == 'POST':
        # Logic to update the campaign in the database
        name = request.form['name']
        const = request.form['constituency']
        start = request.form['start_date']
        end = request.form['end_date']
        
        s_dt = datetime.strptime(start, "%Y-%m-%dT%H:%M")
        e_dt = datetime.strptime(end, "%Y-%m-%dT%H:%M")
        status = "Active" if s_dt <= datetime.now() <= e_dt else "Upcoming"
        
        query = "UPDATE campaigns SET CampaignName = %s, ConstituencyName = %s, StartDate = %s, EndDate = %s, Status = %s WHERE CampaignID = %s"
        db.update(query, (name, const, s_dt, e_dt, status, campaign_id))
        flash('Campaign updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    # On a GET request, fetch existing data and show the form pre-filled.
    campaign = db.fetch("SELECT * FROM campaigns WHERE CampaignID = %s", (campaign_id,))[0]
    return render_template('campaign_form.html', form_action='Update', campaign=campaign)

@app.route('/admin/campaign/delete', methods=['POST'])
@admin_required
def delete_campaign():
    """Deletes a campaign and all its related data."""
    campaign_id = request.form['campaign_id']
    # Use your original, robust deletion logic
    db.update("DELETE v FROM votes v JOIN candidates c ON v.CandidateIDVotedFor = c.CandidateID WHERE c.CampaignID = %s", (campaign_id,))
    db.update("DELETE FROM candidates WHERE CampaignID = %s", (campaign_id,))
    db.update("DELETE FROM campaigns WHERE CampaignID = %s", (campaign_id,))
    flash('Campaign and all related data deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/campaign/<campaign_id>/candidates', methods=['GET', 'POST'])
@admin_required
def manage_candidates(campaign_id):
    """Page to view and add candidates to a specific campaign."""
    if request.method == 'POST':
        # Add a new candidate
        pid = request.form['pid']
        name = request.form['name']
        party = request.form['party']
        query = "INSERT INTO candidates (CampaignID, CandidateID, CandidateName, PartyName) VALUES (%s, %s, %s, %s)"
        db.update(query, (campaign_id, pid, name, party))
        flash('Candidate added successfully.', 'success')
        return redirect(url_for('manage_candidates', campaign_id=campaign_id))
    
    # On a GET request, display the campaign info, existing candidates, and the "add" form.
    campaign = db.fetch("SELECT CampaignName FROM campaigns WHERE CampaignID = %s", (campaign_id,))[0]
    candidates = db.fetch("SELECT * FROM candidates WHERE CampaignID = %s", (campaign_id,))
    return render_template('manage_candidates.html', campaign=campaign, campaign_id=campaign_id, candidates=candidates or [])

@app.route('/admin/results/<campaign_id>')
@admin_required
def view_results(campaign_id):
    """Displays the final results for a completed campaign."""
    campaign = db.fetch("SELECT * FROM campaigns WHERE CampaignID = %s", (campaign_id,))[0]
    # Ensure results are only shown for completed campaigns
    if campaign['Status'] != 'Completed':
        flash('Results are not yet published for this campaign.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # A better query that includes candidates with 0 votes
    query = """
        SELECT c.CandidateName, c.PartyName, COUNT(v.VoteID) AS TotalVotes
        FROM candidates c
        LEFT JOIN votes v ON c.CandidateID = v.CandidateIDVotedFor
        WHERE c.CampaignID = %s
        GROUP BY c.CandidateID
        ORDER BY TotalVotes DESC
    """
    results = db.fetch(query, (campaign_id,))
    return render_template('view_results.html', campaign=campaign, results=results or [])

@app.route('/admin/publish/<campaign_id>', methods=['POST'])
@admin_required
def publish_results(campaign_id):
    """Changes a campaign's status to 'Completed'."""
    db.update("UPDATE campaigns SET Status = 'Completed' WHERE CampaignID = %s", (campaign_id,))
    flash("Results have been published!", "success")
    return redirect(url_for('admin_dashboard'))


# --- Voter Routes ---

@app.route('/voter/dashboard')
@voter_required # Protected route
def voter_dashboard():
    """The main dashboard for the voter, showing active campaigns."""
    voter_id = session['voter_id']
    # Fetch active campaigns
    active_campaigns = db.fetch("SELECT * FROM campaigns WHERE Status = 'Active'")
    # Fetch IDs of campaigns the user has already voted in
    voted_in = db.fetch("SELECT CampaignID FROM votes WHERE VoterID = %s", (voter_id,))
    voted_ids = {item['CampaignID'] for item in voted_in} if voted_in else set()

    return render_template('voter_dashboard.html', campaigns=active_campaigns or [], voted_ids=voted_ids)

@app.route('/voter/vote/<campaign_id>', methods=['GET', 'POST'])
@voter_required
def vote(campaign_id):
    """Page for a voter to cast their vote in a specific campaign."""
    voter_id = session['voter_id']
    
    # Prevent voting twice
    if db.fetch("SELECT 1 FROM votes WHERE VoterID = %s AND CampaignID = %s", (voter_id, campaign_id)):
        flash("You have already voted in this campaign.", "warning")
        return redirect(url_for('voter_dashboard'))
        
    if request.method == 'POST':
        candidate_id = request.form.get('candidate_id')
        # Record the vote in the database
        db.update("INSERT INTO votes (VoterID, CampaignID, CandidateIDVotedFor) VALUES (%s, %s, %s)",
                  (voter_id, campaign_id, candidate_id))
        flash("Your vote has been recorded successfully!", "success")
        return redirect(url_for('voter_dashboard'))

    # On a GET request, show the list of candidates for voting.
    campaign = db.fetch("SELECT * FROM campaigns WHERE CampaignID = %s", (campaign_id,))[0]
    candidates = db.fetch("SELECT * FROM candidates WHERE CampaignID = %s", (campaign_id,))
    return render_template('vote_page.html', campaign=campaign, candidates=candidates or [])

# --- Main execution point ---
if __name__ == '__main__':
    # debug=True allows for automatic reloading when you save changes.
    # Do NOT use debug=True in a production environment.
    app.run(debug=True)
