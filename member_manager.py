import json
import os
import logging

logger = logging.getLogger(__name__)

class MemberManager:
    def __init__(self):
        self.members_file = 'members.json'
        self.initialize_members_file()
        self.members = self.load_members()

    def initialize_members_file(self):
        """Create members.json if it doesn't exist"""
        if not os.path.exists(self.members_file):
            with open(self.members_file, 'w') as f:
                json.dump({}, f, indent=4)
            logger.info(f"Created new {self.members_file} file")

    def load_members(self):
        """Load member data from the JSON file"""
        try:
            with open(self.members_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error reading {self.members_file}, creating new file")
            self.initialize_members_file()
            return {}

    def save_members(self):
        """Save member data to the JSON file"""
        with open(self.members_file, 'w') as f:
            json.dump(self.members, f, indent=4)
        # Refresh the data after saving
        self.members = self.load_members()

    def add_note(self, username, note):
        """Add a note for a user"""
        if username not in self.members:
            self.members[username] = {"notes": [], "names": []}
        
        if "notes" not in self.members[username]:
            self.members[username]["notes"] = []
            
        self.members[username]["notes"].append(note)
        self.save_members()
        return True

    def remove_note(self, username, note_index):
        """Remove a note for a user by index"""
        if username in self.members and "notes" in self.members[username]:
            try:
                note_index = int(note_index)
                if 0 <= note_index < len(self.members[username]["notes"]):
                    removed_note = self.members[username]["notes"].pop(note_index)
                    self.save_members()
                    return True, removed_note
            except ValueError:
                pass
        return False, None

    def add_name(self, username, name):
        """Add a name for a user"""
        if username not in self.members:
            self.members[username] = {"notes": [], "names": []}
        
        if "names" not in self.members[username]:
            self.members[username]["names"] = []
            
        if name not in self.members[username]["names"]:
            self.members[username]["names"].append(name)
            self.save_members()
            return True
        return False

    def get_user_data(self, username):
        """Get all data for a user"""
        return self.members.get(username, {"notes": [], "names": []})

    def get_all_members(self):
        """Get all member data"""
        return self.members 