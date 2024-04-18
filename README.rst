GUIDED RUBRIC XBlock
=====================

This README provides instructions for setting up and using the Guided Rubric XBlock.

Setting Up OpenAI Secret Key Plugin
-----------------------------------

To configure the OpenAI secret key plugin, follow these steps:

1. Create a plugin directory:   
mkdir -p "$(tutor plugins printroot)"

2. Create a file named `openai_key.py` in the plugin directory:
touch "$(tutor plugins printroot)/openai_key.py"

3. List available plugins to verify the new plugin:
tutor plugins list

4. Enable the `openai_key` plugin:
tutor plugins enable openai_key

5. Verify that the plugin is successfully installed:
tutor plugins list

6. Open the created plugin file `~/.local/share/tutor-plugins/openai_key.py` and add the following content:

```python
from tutor import hooks

hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-common-settings",
        "FEATURES['OPENAI_SECRET_KEY'] = 'YOUR_OPENAI_SECRET_KEY'"
    )
)

7. Save the configuration changes:
tutor config save

8. Verify that the setting has been properly added:
grep -r OPENAI_SECRET_KEY "$(tutor config printroot)/env"

9. Restart the local environment:
tutor local restart


Using the Guided Rubric XBlock
1. Access the LMS and CMS containers.
2. Clone the repository into the EDX platform of CMS and LMS.
3. Navigate to the following path: /openedx/edx-platform
4. Install the XBlock using pip:
pip install -e guidedrubric-xblock

5. Restart the LMS and CMS containers:
tutor local restart lms cms

6. Access the Studio and add "guidedrubric" in advance module list of advanced settings of the course.
7. Save the settings and navigate to the course outline.
8. Add a unit and select the "Advanced" tab. You will see "guidedrubric" in the dropdown menu.
