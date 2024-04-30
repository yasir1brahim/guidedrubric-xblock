"""TO-DO: Write a description of what this XBlock is."""

from typing_extensions import override
from django.conf import settings
from django.contrib.auth.models import User
from django.template import Context, Template
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import Q
from django.utils.module_loading import import_string
from webob import Response
from six import string_types
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.completable import CompletableXBlockMixin
from xblock.fields import Scope, String, Float, Boolean, Dict, DateTime, Integer
import zipfile
import os
import logging
import pkg_resources
import openai
from openai import AssistantEventHandler
from dotenv import load_dotenv
import time
import re
import json
from xblock.fields import Scope, String, Integer
from django.template import Context, Template
from xblock.completable import CompletableXBlockMixin
from webob import Response
import logging
from xblock.completable import CompletableXBlockMixin
from webob import Response
import logging
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)

from xblockutils.resources import ResourceLoader
loader = ResourceLoader(__name__)

try:
    try:
        from common.djangoapps.student.models import CourseEnrollment
    except RuntimeError:
        # Older Open edX releases have a different import path
        from student.models import CourseEnrollment
    from lms.djangoapps.courseware.models import StudentModule
except ImportError:
    CourseEnrollment = None
    StudentModule = None



load_dotenv()
client = openai.OpenAI(api_key=settings.FEATURES['OPENAI_SECRET_KEY'])
model = "gpt-4-turbo-preview"

ai_messages = []
ai_grade = []
# First, we create a EventHandler class to define
# how we want to handle the events in the response stream.


def _(text):
    return text

class EventHandler(AssistantEventHandler):    
  def __init__(self, grade=False):
        super().__init__()
        self.grade = grade
  @override
  def on_text_created(self, text) -> None:
    pass
    # print(f"\nassistant > ", end="", flush=True)
      
  @override
  def on_text_delta(self, delta, snapshot):
    logging.info('=========on_text_delta')
    logging.info(delta.value)
    if delta.value:
        if self.grade:
            ai_grade.append(delta.value)
        else:
            ai_messages.append(delta.value)
            logging.info('========append ai_message')
            logging.info(ai_messages)
      
  def on_tool_call_created(self, tool_call):
    pass
    # print(f"\nassistant > {tool_call.type}\n", flush=True)
  
  def on_tool_call_delta(self, delta, snapshot):
    if delta.type == 'code_interpreter':
      if delta.code_interpreter.input:
        print(delta.code_interpreter.input, end="", flush=True)
      if delta.code_interpreter.outputs:
        print(f"\n\noutput >", flush=True)
        for output in delta.code_interpreter.outputs:
          if output.type == "logs":
            print(f"\n{output.logs}", flush=True)
 
# Then, we use the `create_and_stream` SDK helper 
# with the `EventHandler` class to create the Run 
# and stream the response.

phases = [
    {
        "id": "name",
        "question": """What is your name?""",
        "sample_answer": "",
        "instructions": """The user will give you their name. Then, welcome the user to the exercise, and explain that you'll help them and provide feedback as they go. End your statement with "I will now give you your first question about the article." """,
        "rubric": """
            1. Name
                    1 point - The user has provided a response in this thread. 
                    0 points - The user has not provided a response. 
        """,
        "label": "GO!",
        "minimum_score": 0
    },
    {
        "id": "about",
        "question": """What is the article about?""",
        "sample_answer":"This article investigates the impact of various video production decisions on student engagement in online educational videos, utilizing data from 6.9 million video watching sessions on the edX platform. It identifies factors such as video length, presentation style, and speaking speed that influence engagement, and offers recommendations for creating more effective educational content.",
        "instructions": "Provide helpful feedback for the following question. If the student has not answered the question accurately, then do not provide the correct answer for the student. Instead, use evidence from the article coach them towards the correct answer. If the student has answered the question correctly, then explain why they were correct and use evidence from the article. Question:",
        "rubric": """
                1. Length
                    1 point - Response is greater than or equal to 150 characters.
                    0 points - Response is less than 150 characters. 
                2. Key Points
                    2 points - The response mentions both videos AND student engagement rates
                    1 point - The response mentions either videos OR student engagement rates, but not both
                    0 points - The response does not summarize any important points in the article. 
        """,
        "minimum_score": 2
    },
    {
       "id": "methdologies",
       "question": "Summarize the methodology(s) used.",
       "sample_answer": "The study gathered data around video watch duration and problem attempts from the edX logs. These metrics served as a proxy for engagement. Then it compared that with video attributes like length, speaking rate, type, and production style, to determine how video production affects engagement.",
       "instructions": "Provide helpful feedback for the following question. If the student has not answered the question accurately, then do not provide the correct answer for the student. Instead, use evidence from the article coach them towards the correct answer. If the student has answered the question correctly, then explain why they were correct and use evidence from the article. Question:",
       "rubric": """
               1. Correctness
                   1 point - Response is correct and based on facts in the paper
                   0 points - Response is incorrect or not based on facts in the paper
               """,
       "minimum_score": 1
    },
    {
        "id": "findings",
        "question": "What were the main findings in the article?",
        "sample_answer": "Shorter videos are more engaging; Faster-speaking instructors hold students' attention better; High production value does not necessarily correlate with higher engagement;",
        "instructions": "Provide helpful feedback for the following question. If the student has not answered the question accurately, then do not provide the correct answer for the student. Instead, use evidence from the article coach them towards the correct answer. If the student has answered the question correctly, then explain why they were correct and use evidence from the article. Question:",
        "rubric": """
            1. Correctness
                    2 points - Response includes two or more findings or recommendations from the study
                    1 point - Response includes only one finding or recommendation form the study
                    0 points - Response includes no findings or recommendations or is not based on facts in the paper
                    """,
        "minimum_score": 1
    },
    {
        "id": "limitations",
        "question": "What are some of the weaknesses of this study?",
        "sample_answer": "The study cannot measure true student engagement, and so it must use proxies; The study could not track any offline video viewing; The study only used data from math/science courses;",
        "instructions": "Provide helpful feedback for the following question. If the student has not answered the question accurately, then do not provide the correct answer for the student. Instead, use evidence from the article coach them towards the correct answer. If the student has answered the question correctly, then explain why they were correct and use evidence from the article. Question:",
        "rubric": """
            1. Correctness
                    2 points - Response includes two or more limitations of the study
                    1 point - Response includes only one limitation in the study
                    0 points - Response includes no limitations or is not based on facts in the paper
                2. Total Score
                    The total sum of their scores. 
            """,
        "minimum_score": 1
    }
    #Add more steps as needed
    
]

session_state = {
    "current_question_index": 0,
    "thread_obj": None,
    # Add more session state variables as needed
}

current_question_index = session_state['current_question_index'] if 'current_question_index' in session_state else 0

class AssistantManager:
    thread_id = None
    assistant_id = None

    if 'current_question_index' not in session_state:
        session_state.thread_obj = []


    def __init__(self, model: str = model):
        self.client = client
        self.model = model
        self.assistant = None
        self.thread = None
        self.run = None
        self.summary = None

        # Retrieve existing assistant and thread if IDs are already set
        if AssistantManager.assistant_id :
            self.assistant = self.client.beta.assistants.retrieve(
                assistant_id=AssistantManager.assistant_id
            )
        if AssistantManager.thread_id:
            self.thread = self.client.beta.threads.retrieve(
                thread_id=AssistantManager.thread_id
            )

    def create_assistant(self, name, instructions, tools):
        if not self.assistant:
            assistant_obj = self.client.beta.assistants.create(
                name=name, instructions=instructions, tools=tools, model=self.model
            )
            AssistantManager.assistant_id = assistant_obj.id
            self.assistant = assistant_obj
            print(f"AssisID:::: {self.assistant.id}")

    def create_thread(self):
        if not self.thread:
            if session_state['thread_obj']:
                print(f"Grabbing existing thread...")
                thread_obj = session_state['thread_obj']
            else:
                print(f"Creating and saving new thread")
                thread_obj = self.client.beta.threads.create()
                session_state['thread_obj'] = thread_obj

            AssistantManager.thread_id = thread_obj.id
            self.thread = thread_obj
            print(f"ThreadID::: {self.thread.id}")
            return self.thread.id

    def add_message_to_thread(self, role, content):
        if self.thread:
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id, role=role, content=content
            )

    def run_assistant(self, instructions, grade):
        logging.info('===========inside run_assistant')
        logging.info(self.thread)
        logging.info(self.assistant)
        if self.thread and self.assistant:
            logging.info('======run_assistant if ==========')
            try:
                with self.client.beta.threads.runs.create_and_stream(
                    thread_id=self.thread.id,
                    assistant_id=self.assistant.id,
                    instructions=instructions,
                    event_handler=EventHandler(grade=grade),
                ) as stream:
                    stream.until_done()
                    self.run = stream._AssistantEventHandler__current_run
                    self.process_message()
            except Exception as e:
                logging.info('==========error')
                logging.info(e)
                print(f"Streaming error: {e}")

    def process_message(self):
        if self.thread:
            messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
            summary = []

            last_message = messages.data[0]
            role = last_message.role
            response = last_message.content[0].text.value
            summary.append(response)

            self.summary = "\n".join(summary)
            
    def call_required_functions(self, required_actions):
        if not self.run:
            return
        tool_outputs = []

        for action in required_actions["tool_calls"]:
            func_name = action["function"]["name"]
            arguments = json.loads(action["function"]["arguments"])

            if func_name == "respond":
                output = respond(structured_response=arguments["structured_response"])
            
                final_str = ""
                for item in output:
                    final_str += "".join(item)

                tool_outputs.append({"tool_call_id": action["id"], "output": final_str})
            else:
                raise ValueError(f"Unknown function: {func_name}")

        print("Submitting outputs back to the Assistant...")
        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread.id, run_id=self.run.id, tool_outputs=tool_outputs
        )

    def get_summary(self):
        return self.summary

    def wait_for_completion(self):
        if self.thread and self.run:
            while True:
                time.sleep(5)
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id, run_id=self.run.id
                )

                if run_status.status == "completed":
                    self.process_message()
                    break
                elif run_status.status == "requires_action":
                    self.call_required_functions(
                        required_actions=run_status.required_action.submit_tool_outputs.model_dump()
                    )


def extract_score(text):
    # Define the regular expression pattern
    #regex has been modified to grab the total value whether or not it is returned inside double quotes. The AI seems to fluctuate between using quotes around values and not. 
    pattern = r'"total":\s*"?(\d+)"?'
    
    # Use regex to find the score pattern in the text
    match = re.search(pattern, text)

    # If a match is found, return the score, otherwise return None
    if match:
        return int(match.group(1))
    else:
        return 0

def check_score(score, question_num):
    if score >= phases[question_num]["minimum_score"]:
        return True
    else:
        return False

def handle_skip(index):
    session_state[f"phase_{index}_state"] = "skip"
    session_state['current_question_index'] += 1

def build_instructions(index, graded_step=False):
    if graded_step:
        compiled_instructions = """Please provide a score for the previous user message in this thread. Use the following rubric:
        """ + phases[index]["rubric"] + """
        Please output your response as JSON, using this format: { "[criteria 1]": "[score 1]", "[criteria 2]": "[score 2]", "total": "[total score]" }"""
    else:
        compiled_instructions = phases[index]["instructions"] + phases[index]["question"]

    return compiled_instructions

def handle_assistant_grading(index, manager):

    instructions = build_instructions(index, True)
    manager.run_assistant(instructions, True)

    # manager.wait_for_completion()
    summary = manager.get_summary()
    session_state[f"phase_{index}_rubric"] = summary

    score = extract_score(str(summary))
    session_state[f"phase_{index}_score"] = score

    #If the score passes, then increase the index to move to the next step                
    if check_score(score, index):
        session_state['current_question_index'] += 1
        session_state[f"phase_{index}_state"] = "Success"
    else:
        session_state[f"phase_{index}_state"] = "Fail"
    return session_state[f"phase_{index}_state"]

def handle_assistant_interaction(index, manager, user_input):
    manager.add_message_to_thread(
        role="user", content=user_input
    )
    instructions = build_instructions(index)
    logging.info('===========instructions')
    logging.info(instructions)
    manager.run_assistant(instructions, False)
    # manager.wait_for_completion()
    summary = manager.get_summary()
    session_state[f"phase_{index}_summary"] = summary
    return summary

def main(user_input):

    #Create the assistant one time. Only if the Assistant ID is not found, create a new one. 
    manager = AssistantManager()
    manager.create_assistant(
    name="",
    instructions="""""",
    tools=[],
    )
    manager.create_thread()
    
    if  session_state['current_question_index'] <= len(phases) - 1:
        index = session_state['current_question_index']
        if user_input == "skip":
            handle_skip(index)
            hand_intr = None
            hand_gra = None
        elif session_state['current_question_index'] <= len(phases):
            hand_intr = handle_assistant_interaction(index, manager, user_input)
            hand_gra = handle_assistant_grading(index, manager)
        try:
            question = phases[session_state['current_question_index']]['question']
        except:
            question = None
        messages_to_send = ai_messages.copy()
        ai_messages.clear()
        return hand_intr, hand_gra, question, messages_to_send

@XBlock.wants("settings")
@XBlock.wants("user")
class GuidedRubricXBlock(XBlock, CompletableXBlockMixin):
    """
    TO-DO: document what your XBlock does.
    """

    # Fields are defined on the class.  You can access them in your code as
    # self.<fieldname>.

    # TO-DO: delete count, and define your own fields.

    

    assistant_name = String(
        display_name=_("Assistant Name"),
        help=_("Assistan Name"),
        default="",
        scope=Scope.settings,
    )

    phases = String(
        scope=Scope.settings,
        help="The phases to display to a student.",
        default="[]"
    )

    last_phase_id = Integer(
        scope=Scope.settings,
        default=0,
    )


    helper_text = String(
        scope=Scope.content
    )


    last_attempted_phase_id = Integer(
        scope=Scope.user_state,
        default=1,
    )

    open_ai_thread_id = String(
        scope=Scope.user_state,
        default="",
    )

    user_response = Dict(
        scope=Scope.user_state,
        default={},
    )
    
    is_staff = Boolean(
        display_name=_("Is Staff"),
        default=False,
        scope=Scope.settings,
    )

    completion_token = Integer(
        display_name=_("Total Prompt Attempts For User"),
        scope=Scope.user_state,
        default=0,
        help=_("Define how many time a user can make prompts")
    )

    assistant_instructions = String(
        display_name=_("Assistant Instructions"),
        help=_("Assistant Instructions"),
        default="",
        scope=Scope.settings,
    )

    # Non-editable model field for ChatGPT version
    assistant_model = String(
        display_name=_("Model"),
        help=_("The version of ChatGPT currently used by the XBlock"),
        default="ChatGPT4",
        scope=Scope.content,
        edit=False,
    )

    assistant_id = String(
        display_name=_("Assistant ID"),
        help=_("This ID will be auto-generated"),
        default="",
        scope=Scope.content,
        edit=False,
    )

    knowledge_base =  String(
        display_name=_("Knowledge Base"),
        help=_("Knowledge Base"),
        default="",
        scope=Scope.settings,
    )

    zip_file =  String(
        display_name=_("zip_file"),
        help=_("zip_file"),
        default="",
        scope=Scope.settings,
    )

    completion_message =  String(
        display_name=_("Completion Message"),
        help=_("Completion Message"),
        default="",
        scope=Scope.settings,
    )

    max_tokens_per_user = Integer(
        display_name=_("Max Attempts Per User"),
        help=_("Max Tokens Per User"),
        default=0,
        scope=Scope.settings,

    )


    is_last_phase_successful = Boolean(default=False, scope=Scope.user_state)


    @property
    def block_phases(self):
        #logging.info('==========phases property')
        #logging.info(self.phases)
        phases_or_serialized_phases = self.phases

        if phases_or_serialized_phases is None:
            phases_or_serialized_phases = ''

        try:
            phases = json.loads(phases_or_serialized_phases)
        except Exception as e:
            logging.info('============error')
            logging.info(e)
            phases = []
        logging.info('========phases')
        logging.info(phases)
        #logging.info(type(phases))
        return phases

    

    def user_response_details(self):
        user_response = {}
        for phase_id, response in self.user_response.items():
            phase = self.get_phase(int(phase_id))
            if phase:
                question = phase['phase_question']
                user_response.update({int(phase_id): {'question': question, 'response': response}})
        
        return user_response

    
    def get_next_question(self):
        logging.info('=========self')
        logging.info(self)
        logging.info(self.last_attempted_phase_id)
        next_phase_id = self.last_attempted_phase_id
        for item in self.block_phases:
            phase_id = int(item.get('phase_id'))
            logging.info('=========phase_id == next_phase_id')
            logging.info(phase_id == next_phase_id)
            if phase_id == next_phase_id:
                logging.info('=========question is')
                logging.info(item.get('phase_question'))
                return item.get('phase_question')


    @staticmethod
    def json_response(data):
        return Response(
            json.dumps(data), content_type="application/json", charset="utf8"
        )

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def render_template(self, template_path, context):
        template_str = self.resource_string(template_path)
        template = Template(template_str)
        return template.render(Context(context))

    
    
    
    # TO-DO: change this view to display your data your own way.
    def studio_view(self, context=None):
        studio_context = {
            "field_assistant_name": self.fields["assistant_name"],
            "field_assistant_id": self.fields["assistant_id"],
            "field_assistant_instructions": self.fields["assistant_instructions"],
            "field_assistant_model": self.fields["assistant_model"],
            "field_completion_message": self.fields["completion_message"],
            "field_completion_token": self.fields["completion_token"],
            "field_max_tokens_per_user": self.fields["max_tokens_per_user"],
            "field_zip_file":self.fields["zip_file"],
            "guided_rubric_xblock": self
            
        }

        studio_context.update(context or {})
        template = self.render_template("static/html/studio.html", studio_context)
        frag = Fragment(template)


        # html = self.resource_string("static/html/guidedrubric.html")
        # html = self.resource_string("static/html/studio.html")
        # frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/studio.css"))
        frag.add_javascript(self.resource_string("static/js/src/studio.js"))
        frag.initialize_js('GuidedRubricXBlock')
        return frag
    
    @staticmethod
    def json_response(data):
        return Response(
            json.dumps(data), content_type="application/json", charset="utf8"
        )

    @XBlock.handler
    def studio_submit(self, request, _suffix):
        print("REQUEST PARAMS", request.params)
        self.phases = json.dumps(json.loads(request.params['phases']))
        self.last_phase_id = request.params["last_phase_id"]
        self.assistant_name = request.params["assistant_name"]
        self.assistant_instructions = request.params["assistant_instructions"]
        self.assistant_model = request.params["assistant_model"]
        if type(request.params["knowledge_base"]) != str:
            self.knowledge_base = request.params["knowledge_base"].file._name
        self.completion_message = request.params["completion_message"]
        self.max_tokens_per_user = request.params["max_tokens_per_user"]

        manager = AssistantManager()
        response = {"result": "success", "errors": []}

        if self.assistant_id:
            try:
                client.beta.assistants.update(
                    self.assistant_id,
                    instructions=self.assistant_instructions,
                    name=self.assistant_name,
                    tools=[{"type": "retrieval"}],  # Assuming this is the tool configuration
                    model="gpt-4-turbo-preview"
                )
                response["message"] = "Assistant updated successfully."
            except Exception as e:
                print(e)
                response["errors"].append("Failed to update the assistant.")
        else:
            try:
                manager.create_assistant(
                    name=self.assistant_name,
                    instructions=self.assistant_instructions,
                    tools=[{"type": "retrieval"}]
                )
                self.assistant_id = manager.assistant_id
                response["message"] = "Assistant created successfully."
            except Exception as e:
                print(e)
                response["errors"].append("Failed to create the assistant.")

        # Handling knowledge base upload and association with the assistant
        if type(request.params["knowledge_base"]) != str:
            knowledge_base_file = request.params.get("knowledge_base")
            if knowledge_base_file:
                try:
                    package_file = knowledge_base_file.file
                    dest_path_2 = os.path.join(self.extract_folder_base_path, knowledge_base_file.filename)
                    self.storage.save(dest_path_2, package_file)
                    self.zip_file = settings.LMS_ROOT_URL+'/'+'media'+'/'+dest_path_2

                    extracted_files = self.extract_package(package_file)

                    for file_path in extracted_files:
                        with open(file_path, 'rb') as file:
                            uploaded_file = client.files.create(file=file, purpose='assistants')

                        client.beta.assistants.files.create(assistant_id=self.assistant_id, file_id=uploaded_file.id)

                except Exception as e:
                    print(e)
                    response["errors"].append("Knowledge base file not provided.")
            elif self.zip_file:  # Use previously uploaded file if available
                try:
                    # Associate the previously uploaded file with the assistant
                    uploaded_file = client.files.create(filename=self.knowledge_base, purpose='assistants')
                    client.beta.assistants.files.create(assistant_id=self.assistant_id, file_id=uploaded_file.id)
                except Exception as e:
                    print(e)
                    response["errors"].append("Failed to associate previously uploaded knowledge base file.")

        return self.json_response(response)

    
    def extract_package(self, package_file):
        extracted_files = []  # Initialize list to store extracted file paths
        
        with zipfile.ZipFile(package_file, "r") as scorm_zipfile:
            zipinfos = scorm_zipfile.infolist()
            root_path = None
            root_depth = -1
            for zipinfo in zipinfos:
                depth = len(os.path.split(zipinfo.filename))
                if depth < root_depth or root_depth < 0:
                    root_path = os.path.dirname(zipinfo.filename)
                    root_depth = depth

            for zipinfo in zipinfos:
                # Extract only files that are below the root
                if zipinfo.filename.startswith(root_path) and not zipinfo.filename.endswith("/"):
                    dest_path = os.path.join(
                        self.extract_folder_path,
                        os.path.relpath(zipinfo.filename, root_path),
                    )
                    dest_path_2 = os.path.join(
                    settings.MEDIA_ROOT,  # Prepend MEDIA_ROOT to the destination path
                    self.extract_folder_path,
                    os.path.relpath(zipinfo.filename, root_path),
                )

                    self.storage.save(
                        dest_path,
                        ContentFile(scorm_zipfile.read(zipinfo.filename)),
                    )                   
                    # Append the extracted file path to the list
                    extracted_files.append(dest_path_2)
                        
        # Return the list of extracted file paths
        return extracted_files
    
            
    @property
    def extract_folder_path(self):
        """
        This path needs to depend on the content of the scorm package. Otherwise,
        served media files might become stale when the package is update.
        """
        return os.path.join(self.extract_folder_base_path)
    
    @property
    def extract_folder_base_path(self):
        """
        Path to the folder where packages will be extracted.
        """
        return os.path.join(self.scorm_location(), self.location.block_id)


    def get_phase(self, phase_id):
        for item in self.block_phases:
            if int(item.get('phase_id')) == phase_id:
                return item
    
    def get_next_phase_id(self):
        logging.info('==========inside get_next_phase_id')
        for item in self.block_phases:
            phase_id = int(item.get('phase_id'))
            logging.info('====phase id')
            logging.info(phase_id)
            logging.info(type(phase_id))
            if phase_id != int(self.last_attempted_phase_id) and phase_id > int(self.last_attempted_phase_id):
                logging.info('==========get_next_phase_id')
                logging.info(phase_id)
                return phase_id
    


        
    def scorm_location(self):
        """
        Unzipped files will be stored in a media folder with this name, and thus
        accessible at a url with that also includes this name.
        """

        default_scorm_location = "guided-rubric"
        return self.xblock_settings.get("LOCATION", default_scorm_location)

    
    @XBlock.handler
    def scorm_search_students(self, data, _suffix):
        print("=============scorm_search_students===========")
        """
        Search enrolled students by username/email.
        """
        query = data.params.get("id", "")
        print("query", query)
        enrollments = (
            CourseEnrollment.objects.filter(
                is_active=True,
                course=self.runtime.course_id,
            )
            .select_related("user")
            .order_by("user__username")
        )
        print("enrollments", enrollments)
        if query:
            enrollments = enrollments.filter(
                Q(user__username__startswith=query) | Q(user__email__startswith=query)
            )
            print("enrollments====>", enrollments)
        # The format of each result is dictated by the autocomplete js library:
        # https://github.com/dyve/jquery-autocomplete/blob/master/doc/jquery.autocomplete.txt
        return self.json_response(
            [
                {
                    "data": {"student_id": enrollment.user.id},
                    "value": f"{enrollment.user.username} ({enrollment.user.email})"
                }
                for enrollment in enrollments[:20]
            ]
        )

    @XBlock.handler
    def scorm_get_student_state(self, data, _suffix):
        print("scorm_get_student_state")
        user_id = data.params.get("id")
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return Response(
                body=f"Invalid 'id' parameter {user_id}", status=400
            )
        try:
            user = User.objects.get(id=user_id)
            if user:
                print("SELF COMPLETION TOKEN", self.completion_token)
                self.completion_token = 0
        except Exception as e:
            print(e)
        
        response_metadata = {'completion_token': self.completion_token}
        print("COMPLETION TOKENSS", self.completion_token)

        return self.json_response({'result': 'success','response_metadata':response_metadata})

    
    
    def student_view(self, context=None):
        """
        The primary view of the GuidedRubricXBlock, shown to students
        when viewing courses.
        """
        if len(self.user_response.keys()) == 0:
            try:
                self.last_attempted_phase_id = int(self.block_phases[0]['phase_id'])
            except:
                self.last_attempted_phase_id = 1
        is_initial_phase = True
        if len(self.user_response.keys()) > 0:
            is_initial_phase = False
        #self.completion_token = 0
            #self.user_response = {}
        logging.info('=======user_response1')
        #self.user_response = {1: 'skip'}
        logging.info(self.user_response)
        user_service = self.runtime.service(self, 'user')
        xb_user = user_service.get_current_user()
        user_role = xb_user.opt_attrs['edx-platform.user_is_staff']
        print("xb_user.opt_attrs['edx-platform.user_is_staff']",user_role)
        is_user_staff = False
        if user_role:
            is_user_staff = True
        else:
            is_user_staff = False

        next_phase_id = self.get_next_phase_id()
        #self.is_last_phase_successful = True
        phase = self.get_phase(self.last_attempted_phase_id)
        button_label = ''
        if phase:
            button_label = phase['button_label']
        
        logging.info('======self.get_next_question()')
        logging.info(self.get_next_question())
        lms_context = {
            "guided_rubric_xblock": self,
            "next_question": self.get_next_question(),
            'user_response_details': self.user_response_details(),
            "button_label" : button_label,
            'is_user_staff':is_user_staff,
            "is_last_phase_successful": self.is_last_phase_successful,
            "last_attempted_phase_id": self.last_attempted_phase_id,
            "is_initial_phase": is_initial_phase
            # "button_label": self.get_phase(self.last_attempted_phase_id)['button_label'] if self.get_phase(self.last_attempted_phase_id)['button_label'] else "" 
        }
        #context.update(context or {})
        lms_context.update(context or {})
        logging.info('+++++++ lms context ++++++')
        logging.info(lms_context)
        logging.info('=========user_response')
        logging.info(self.user_response_details())
        template = self.render_template("static/html/lms.html", lms_context)
        frag = Fragment(template)
        frag.add_css(self.resource_string("static/css/lms.css"))
        frag.add_javascript(self.resource_string("static/js/src/lms.js"))
        frag.initialize_js('GuidedRubricXBlock')
        return frag


    def build_instructions(self, phase_id, graded_step):
        phase = None
        for item in self.block_phases:
            if int(item.get('phase_id')) == phase_id:
                phase = item
                break
        if graded_step and phase.get('scored_question', None):
            # if phase.get('scored_question', None):
            compiled_instructions = """Please provide a score for the previous user message in this thread. Use the following rubric:
            """ + phase["rubric"] + """
            Please output your response as JSON, using this format: { "[criteria 1]": "[score 1]", "[criteria 2]": "[score 2]", "total": "[total score]" }"""
        else:
            compiled_instructions = phase["ai_instructions"] + phase["phase_question"]

        return compiled_instructions

    
    def handle_assistant_interaction(self, index, manager, user_input):
        manager.add_message_to_thread(
            role="user", content=user_input
        )
        instructions = self.build_instructions(index, False)
        logging.info('===========instructions')
        logging.info(instructions)
        manager.run_assistant(instructions, False)
        # manager.wait_for_completion()
        summary = manager.get_summary()
        #session_state[f"phase_{index}_summary"] = summary
        return summary


    def extract_score(self, text):
        # Define the regular expression pattern
        #regex has been modified to grab the total value whether or not it is returned inside double quotes. The AI seems to fluctuate between using quotes around values and not. 
        pattern = r'"total":\s*"?(\d+)"?'
        
        # Use regex to find the score pattern in the text
        match = re.search(pattern, text)

        # If a match is found, return the score, otherwise return None
        if match:
            return int(match.group(1))
        else:
            return 0

    
    def check_score(self, score, phase_id):
        phase = self.get_phase(phase_id)
        if score >= int(phase["minimum_score"]):
            return True
        else:
            return False
    

    def handle_assistant_grading(self, index, manager):
        phase = self.get_phase(self.last_attempted_phase_id)
        if not phase['scored_question']:
            self.last_attempted_phase_id = self.get_next_phase_id()
            self.is_last_phase_successful = True
            return "Success"
        instructions = self.build_instructions(index, True)
        manager.run_assistant(instructions, True)

        # manager.wait_for_completion()
        summary = manager.get_summary()
        #session_state[f"phase_{index}_rubric"] = summary

        score = self.extract_score(str(summary))
        #session_state[f"phase_{index}_score"] = score

        phase_state = None
        #If the score passes, then increase the index to move to the next step                
        if self.check_score(score, index):
            #session_state['current_question_index'] += 1
            self.last_attempted_phase_id = self.get_next_phase_id()
            phase_state = "Success"
            self.is_last_phase_successful = True
        else:
            phase_state = "Fail"
            self.is_last_phase_successful = False
        return phase_state


    def handle_skip(self):
        self.last_attempted_phase_id = self.get_next_phase_id()


    def handle_interaction(self, user_input):

        AssistantManager.assistant_id = self.assistant_id
        AssistantManager.thread_id = self.open_ai_thread_id
        manager = AssistantManager()
        #manager.assistant_id = self.assistant_id

        if not self.open_ai_thread_id:    
            thread_id = manager.create_thread()
            self.open_ai_thread_id = thread_id
        
        #manager.thread_id = self.open_ai_thread_id
        
        # if  self.last_attempted_phase_id <= self.last_phase_id - 1:
        if True:
            hand_intr = None
            hand_gra = None
            if not self.last_attempted_phase_id:
                return hand_intr, hand_gra, None, None, [], self.completion_message
            else:
                index = int(self.last_attempted_phase_id)
            if user_input == "skip":
                self.handle_skip()
                hand_intr = None
                hand_gra = None
            elif self.last_attempted_phase_id <= self.last_phase_id:
                hand_intr = self.handle_assistant_interaction(index, manager, user_input)
                hand_gra = self.handle_assistant_grading(index, manager)
            try:
                logging.info('=======getting next phase question')
                logging.info(self.last_attempted_phase_id)
                phase = self.get_phase(self.last_attempted_phase_id)
                question = phase['phase_question']
                button_label = phase['button_label']
            except:
                question = None
                button_label = None
            messages_to_send = ai_messages.copy()
            ai_messages.clear()
        return hand_intr, hand_gra, question, button_label, messages_to_send, self.completion_message

    # TO-DO: change this handler to perform your own actions.  You may need more
    # than one handler, or you may not need any handlers at all.
    @XBlock.json_handler
    def send_message(self, data, suffix=""):
        """Send message to OpenAI, and return the response"""

        #self.user_response = {}
        #self.last_attempted_phase_id = 1
        phase = self.get_phase(self.last_attempted_phase_id)
        response_metadata = {'attempted_phase_id': self.last_attempted_phase_id, 'attempted_phase_question':\
        phase['phase_question']}
        self.user_response[self.last_attempted_phase_id] = data['message']
        user_input = data['message']
        phase_id = int(self.last_attempted_phase_id)
        res = self.handle_interaction(user_input)
        if self.user_response.get(phase_id):
            user_response = self.user_response
            # phase_response = user_response[int(self.last_attempted_phase_id)]
            phase_response = {}
            phase_response['user_response'] = data['message']
            phase_response['ai_response'] = res[0]
            user_response[phase_id] = phase_response
            self.user_response = user_response
        else:
            user_response = self.user_response
            phase_response = {}
            phase_response['user_response'] = data['message']
            phase_response['ai_response'] = res[0]
            user_response[phase_id] = phase_response
            self.user_response = user_response
        

        # thread_messages = client.beta.threads.messages.list(self.open_ai_thread_id,
        #                                                     order='desc',
        #                                                     limit=1)
        # latest_message = thread_messages.data[0]
        # run_id = latest_message.run_id
        # runs = client.beta.threads.runs.retrieve(
        # thread_id=self.open_ai_thread_id,
        # run_id=run_id
        # )
        # completion_tokens = runs.usage.completion_tokens
        self.completion_token += 1
        response_metadata.update({'completion_token': self.completion_token,\
        'is_attempted_phase_successful': self.is_last_phase_successful})
        print("COMPLETION TOKENSS", self.completion_token)

        return {'result': 'success' if res else 'failed', 'response': res, 'response_metadata': response_metadata}

    
    @XBlock.json_handler
    def update_last_phase_id(self, data, suffix=""):
        """Send message to OpenAI, and return the response"""
        self.last_attempted_phase_id = data['last_attempted_phase_id']
        res = {'success': True}
        return {'result': 'success' if res else 'failed', 'response': res}

    # TO-DO: change this to create the scenarios you'd like to see in the
    # workbench while developing your XBlock.
    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("GuidedRubricXBlock",
             """<guidedrubric/>
             """),
            ("Multiple GuidedRubricXBlock",
             """<vertical_demo>
                <guidedrubric/>
                <guidedrubric/>
                <guidedrubric/>
                </vertical_demo>
             """),
        ]
    @property
    def storage(self):
        """
        Return the storage backend used to store the assets of this xblock. This is a cached property.
        """
        if not getattr(self, "_storage", None):

            def get_default_storage(_xblock):
                return default_storage

            storage_func = self.xblock_settings.get("STORAGE_FUNC", get_default_storage)
            if isinstance(storage_func, string_types):
                storage_func = import_string(storage_func)
            self._storage = storage_func(self)

        return self._storage

    @property
    def xblock_settings(self):
        """
        Return a dict of settings associated to this XBlock.
        """
        settings_service = self.runtime.service(self, "settings") or {}
        if not settings_service:
            return {}
        return settings_service.get_settings_bucket(self)


def parse_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_float(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_validate_positive_float(value, name):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"Could not parse value of '{name}' (must be float): {value}"
        )
    if parsed < 0:
        raise ValueError(f"Value of '{name}' must not be negative: {value}")
    return parsed


class ScormError(Exception):
    pass

