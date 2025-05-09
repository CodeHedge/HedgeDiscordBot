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

    def find_main_username(self, username):
        """Find the main username for a given username or alias"""
        # First check if the username exists directly
        if username in self.members:
            return username

        # Then check all members' aliases
        for main_username, data in self.members.items():
            if "aliases" in data and username in data["aliases"]:
                return main_username

        # If not found, return the original username
        return username

    def add_note(self, username, note):
        """Add a note for a user"""
        main_username = self.find_main_username(username)
        
        if main_username not in self.members:
            self.members[main_username] = {"notes": [], "names": [], "aliases": []}
        
        if "notes" not in self.members[main_username]:
            self.members[main_username]["notes"] = []
            
        self.members[main_username]["notes"].append(note)
        self.save_members()
        return True

    def add_name(self, username, name):
        """Add a name for a user"""
        main_username = self.find_main_username(username)
        
        if main_username not in self.members:
            self.members[main_username] = {"notes": [], "names": [], "aliases": []}
        
        if "names" not in self.members[main_username]:
            self.members[main_username]["names"] = []
            
        if name not in self.members[main_username]["names"]:
            self.members[main_username]["names"].append(name)
            self.save_members()
            return True
        return False

    def add_alias(self, username, alias):
        """Add an alias for a user"""
        main_username = self.find_main_username(username)
        
        if main_username not in self.members:
            self.members[main_username] = {"notes": [], "names": [], "aliases": []}
        
        if "aliases" not in self.members[main_username]:
            self.members[main_username]["aliases"] = []
            
        if alias not in self.members[main_username]["aliases"]:
            self.members[main_username]["aliases"].append(alias)
            self.save_members()
            return True
        return False

    def remove_note(self, username, note_index):
        """Remove a note for a user by index"""
        main_username = self.find_main_username(username)
        
        if main_username in self.members and "notes" in self.members[main_username]:
            try:
                note_index = int(note_index)
                if 0 <= note_index < len(self.members[main_username]["notes"]):
                    removed_note = self.members[main_username]["notes"].pop(note_index)
                    self.save_members()
                    return True, removed_note
            except ValueError:
                pass
        return False, None

    def get_user_data(self, username):
        """Get all data for a user"""
        main_username = self.find_main_username(username)
        return self.members.get(main_username, {"notes": [], "names": [], "aliases": []})

    def get_all_members(self):
        """Get all member data"""
        return self.members

    def get_user_aliases(self, username):
        """Get all aliases for a user"""
        main_username = self.find_main_username(username)
        user_data = self.get_user_data(main_username)
        return user_data.get("aliases", [])

    def delete_user(self, username):
        """Delete a user and all their data from the members file"""
        main_username = self.find_main_username(username)
        
        if main_username in self.members:
            # Store the data before deletion for the return value
            deleted_data = self.members[main_username]
            # Delete the user
            del self.members[main_username]
            # Save the changes
            self.save_members()
            return True, deleted_data
        return False, None 