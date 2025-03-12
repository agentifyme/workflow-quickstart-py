import os
from agentifyme.utilities.modules import load_modules_from_directory
from agentifyme.components.workflow import WorkflowConfig

project_dir = os.getcwd() + "/src"
load_modules_from_directory(project_dir)
info_dict = WorkflowConfig._registry
