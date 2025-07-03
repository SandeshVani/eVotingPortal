create database eVotingMpDb;
use eVotingMpDb;

-- Voters Table

create table voters(
	VoterID varchar(50) primary key,
	Name varchar(200) not null,
	Password varchar(200) not null
);

ALTER TABLE voters
ADD COLUMN FailedAttempts INT DEFAULT 0,
ADD COLUMN BlockUntil DATETIME DEFAULT NULL;

INSERT INTO voters (VoterID, Name, Password) VALUES
('MP001', 'Arjun Mehta', 'arjun123'),
('MP002', 'Sneha Reddy', 'sneha@456'),
('MP003', 'Karan Verma', 'karanPwd'),
('MP004', 'Pooja Sharma', 'pooja@789'),
('MP005', 'Ravi Yadav', 'raviPass1'),
('MP006', 'Simran Kaur', 'simran2024'),
('MP007', 'Ankit Jain', 'ankit_001'),
('MP008', 'Neha Joshi', 'neha#pwd'),
('MP009', 'Mohit Gupta', 'mohit!987'),
('MP010', 'Divya Patel', 'divya321'),
('MP011', 'Yash Thakur', 'yashPass'),
('MP012', 'Preeti Chauhan', 'preeti@123'),
('MP013', 'Suresh Bansal', 'sureshPwd'),
('MP014', 'Tina Kapoor', 'tina789'),
('MP015', 'Nikhil Singh', 'nikhil_456');


-- Campaigns Table

create table campaigns(
	CampaignID varchar(50) primary key,
	CampaignName varchar(200) not null,
	ConstituencyName VARCHAR(200),
	StartDate DATETIME NOT NULL,
	EndDate DATETIME NOT NULL,
    Status VARCHAR(50) DEFAULT 'Upcoming' -- e.g., Upcoming, Active, Ended, Results Published
);

INSERT INTO campaigns (CampaignID, CampaignName, ConstituencyName, StartDate, EndDate, Status) VALUES
-- Completed
('C001', '2024 Local Body Elections', 'Indore North', '2024-01-10 08:00:00', '2024-01-15 17:00:00', 'Completed'),

-- Active campaigns
('C002', '2025 Panchayat Polls', 'Alirajpur', '2025-06-01 08:00:00', '2025-06-05 17:00:00', 'Active'),
('C003', '2025 Assembly Elections', 'Bhopal Central', '2025-06-20 08:00:00', '2025-06-24 17:00:00', 'Active'),
('C004', '2025 City Council Elections', 'Ujjain East', '2025-06-29 08:00:00', '2025-07-02 10:00:00', 'Active'),

-- Upcoming campaign
('C005', '2025 General Elections', 'Gwalior West', '2025-08-10 08:00:00', '2025-08-15 17:00:00', 'Upcoming');

-- Candidate Table

create table candidates(
	CampaignID varchar(50),
	CandidateID varchar(50) primary key,
	CandidateName varchar(200) not null,
	PartySymbol varchar(100),
	PartyName varchar(100) not null,
	foreign key (CampaignID) references campaigns(CampaignID)
);

-- Campaign C001 (Completed)
INSERT INTO candidates (CampaignID, CandidateID, CandidateName, PartySymbol, PartyName) VALUES
('C001', 'C001_C001', 'Meena Solanki', 'Hand', 'Indian National Congress'),
('C001', 'C001_C002', 'Arvind Rawat', 'Lotus', 'Bharatiya Janata Party'),
('C001', 'C001_C003', 'Sunita Chouhan', 'Elephant', 'Bahujan Samaj Party'),

-- Campaign C002
('C002', 'C002_C001', 'Ravi Thakur', 'Broom', 'Aam Aadmi Party'),
('C002', 'C002_C002', 'Anita Yadav', 'Cycle', 'Samajwadi Party'),
('C002', 'C002_C003', 'Suresh Meena', 'Lantern', 'Rashtriya Janata Dal'),

-- Campaign C003
('C003', 'C003_C001', 'Kiran Joshi', 'Bow and Arrow', 'Shiv Sena'),
('C003', 'C003_C002', 'Manoj Verma', 'Rising Sun', 'Dravida Munnetra Kazhagam'),
('C003', 'C003_C003', 'Divya Rathore', 'Sickle and Hammer', 'Communist Party of India'),

-- Campaign C004
('C004', 'C004_C001', 'Nikhil Sharma', 'Two Leaves', 'AIADMK'),
('C004', 'C004_C002', 'Tina Patel', 'Clock', 'Nationalist Congress Party'),
('C004', 'C004_C003', 'Amit Deshmukh', 'Ceiling Fan', 'YSR Congress Party'),

-- Campaign C005 (Upcoming)
('C005', 'C005_C001', 'Priya Singh', 'Torch', 'Samata Party'),
('C005', 'C005_C002', 'Rohit Sinha', 'Hurricane Lamp', 'Janata Dal (Secular)');


-- Votes Table

create table votes(
	VoteID int auto_increment primary key,
    VoterID varchar(50) not null,
    CampaignID varchar(50) not null,
    CandidateIDVotedFor varchar(50) not null,
    Timestamp datetime default current_timestamp,
    foreign key(VoterID) references voters(VoterID),
    foreign key(CampaignID) references campaigns(CampaignID),
    foreign key(CandidateIDVotedFor) references candidates(CandidateID),
    unique(CampaignID, VoterID)  -- Each voter can cast their vote once per campaign
);

