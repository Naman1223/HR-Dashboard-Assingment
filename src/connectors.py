import uuid
import datetime
from abc import ABC, abstractmethod

class OutreachConnector(ABC):
    """Base class for all outreach connectors."""
    
    @abstractmethod
    def send_message(self, profile_id, role_id, message_text):
        """
        Sends an outreach message and returns an entry dictionary for the outreach log.
        """
        pass


class LinkedInMockConnector(OutreachConnector):
    """Mock connector for LinkedIn outreach to simulate success and AUTH_401 failures."""
    
    def __init__(self, force_fail=False):
        self.force_fail = force_fail
        
    def send_message(self, profile_id, role_id, message_text):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        outreach_id = str(uuid.uuid4())[:8].upper()
        
        if self.force_fail:
            return {
                "Outreach_ID": outreach_id,
                "Profile_ID": profile_id,
                "Role_ID": role_id,
                "Created_At": ts,
                "Channel": "LinkedIn",
                "Message_Type": "Initial Outreach",
                "Message_Text": message_text,
                "Approval_Status": "Approved",
                "Send_Status": "Failed",
                "Sent_At": None,
                "Response_Status": "N/A",
                "Error_Code": "AUTH_401",
                "Error_Detail": "Mock connector token expired"
            }
        else:
            return {
                "Outreach_ID": outreach_id,
                "Profile_ID": profile_id,
                "Role_ID": role_id,
                "Created_At": ts,
                "Channel": "LinkedIn",
                "Message_Type": "Initial Outreach",
                "Message_Text": message_text,
                "Approval_Status": "Approved",
                "Send_Status": "Sent",
                "Sent_At": ts,
                "Response_Status": "Pending",
                "Error_Code": None,
                "Error_Detail": None
            }
