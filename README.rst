GUIDED RUBRIC XBlock
=====================

This README provides instructions for setting up and using the Guided Rubric XBlock.

Setting Up OpenAI Secret Key Plugin
-----------------------------------

To configure the OpenAI secret key plugin, follow these steps:

1. Create a plugin directory:

..  code-block:: bash
    
     mkdir -p "$(tutor plugins printroot)"

2. Create a file named `openai_key.py` in the plugin directory:

..  code-block:: bash
    
     touch "$(tutor plugins printroot)/openai_key.py"

3. List available plugins to verify the new plugin:

..  code-block:: bash
    
     tutor plugins list



4. Enable the `openai_key` plugin:

..  code-block:: bash
    
     tutor plugins enable openai_key


5. Verify that the plugin is successfully installed:

..  code-block:: bash
    
     tutor plugins list



6. Open the created plugin file `~/.local/share/tutor-plugins/openai_key.py` and add the following code:


..  code-block:: python
    :caption: EXT:~/.local/share/tutor-plugins/openai_key.py

    from tutor import hooks

        hooks.Filters.ENV_PATCHES.add_items([
            (
                "openedx-common-settings",
                 """
        FEATURES['OPENAI_SECRET_KEY'] = 'YOUR OPENAI_SECRET_KEY'
                 """
            )
        ])
        

7. Save the configuration changes:

..  code-block:: bash
    
     tutor config save


8. Verify that the setting has been properly added:

..  code-block:: bash
    
     grep -r OPENAI_SECRET_KEY "$(tutor config printroot)/env"


9. Restart the platform:

..  code-block:: bash
    
     tutor local restart




USING THE GUIDED RUBRIC XBLOCK
-----------------------------------

1. Access the LMS and CMS containers.

2. Clone the repository into the EDX platform of CMS and LMS.


3. Go in to the cloned folder and checkout to branch feature/guided-rubric

4. Navigate back to edx-platform and Install the XBlock using pip:

   ..  code-block:: bash
    
     pip install -e ai-guided-tutor-xblock-openedx
   

5. Restart the Platform:

   ..  code-block:: bash
    
     tutor local restart

6. Access the Studio and add "guidedrubric" in advance module list of advanced settings of the course.

7. Save the settings and navigate to the course outline.

8. Add a unit and select the "Advanced" tab. You will see "guidedrubric" in the dropdown menu.
