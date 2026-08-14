# Tutorials

This documentation goes over how to use DigitalAgEdu, the machine learning and AI curriculum generator. The application itself enables educators to generate models, content, exercises, and solutions, weaving the domain/dataset specified by the educator.

——————————————————————————————————————————

### Getting Started

This application uses Tapis, if you already have an account and a system authenticated you may skip this section.

1. Navigate to https://icicleai.tapis.io/#/login. You will be prompted to login. Please select **University Accounts (CILogon)**. If you do not have an Access account, you can create one here: https://account.access-ci.org/register 

![Login Page](./documentation/images/image15.png)

2. Select the University that you are affiliated with to log in.

![Select University](./documentation/images/image24.png)

3. After logging in you will be shown the main page for Icicle’s TAPIS.

![Tapis Main Page](./documentation/images/image6.png)

4. To use this application, a system needs to be authenticated. We’ll use SDSC’s Expanse portal for this demonstration: https://portal.expanse.sdsc.edu/ 
   - You may log in using the ACCESS/CILogon account created beforehand.

5. Once logged in, click on **expanse Shell Access**.

![Expanse Shell Access](./documentation/images/image26.png)

6. Inside the terminal, you will need to run these commands:
   ```bash
   ssh-keygen -t rsa -b 4096 -m PEM 
   cd ~/.ssh 
   cat id_rsa.pub
   cat id_rsa
   echo 'export SCRATCH="/expanse/scratch/${USER}"' >> ~/.bashrc
   echo 'export SCRATCH="/expanse/scratch/${USER}"' >> ~/.bash_profile
   ```

   `id_rsa.pub` is your public key and `id_rsa` is your private key. We will be using these to authenticate the Expanse system.

   In the terminal, run `cd ~/.ssh` and `nano authorized_keys` and paste the contents of your public key in. Run `CTRL + X` to save the contents of the file.

![SSH Authorized Keys](./documentation/images/image8.png)

![Saved Public Key](./documentation/images/image3.png)

7. Log back into https://icicleai.tapis.io/ and click on **Systems**.

![Tapis Systems](./documentation/images/image11.png)

8. Click on the **Authenticate** button. The screen below will appear. Paste in your credentials generated from the keys made earlier into **Private key** and **Public key** and enter your username for that system in **Login User**.

![Authenticate System](./documentation/images/image14.png)

![Paste Credentials](./documentation/images/image7.png)

9. Your account should be authenticated now and should show this screen:

![Authenticated Status](./documentation/images/image19.png)

#### Common Issues
1. Double check that the entire public/private key is pasted into the box, including keys that may start with “----------- BEGIN RSA KEY —------------”. It's important to paste that in as well.
2. Ensure in `authorized_keys` your public key is pasted in and saved.
3. Ensure that the system you’re attempting to authenticate is the same system your authorized keys reside in.

——————————————————————————————————————————

### Prerequisites

Please refer to the [YAML Configuration Guide](./YAML_CONFIG_GUIDE.md). This documentation is important as it goes over one of the key inputs for this application to run correctly. 

Additionally, as noted in the YAML Configuration Guide, the application expects a specific dataset structure to run as expected. The program recursively takes each folder inside the directory as a label. For example:

```
    food/
         |_pasta/
             |_pizza/
            |_pepperoni_pizza/
             |_etc./
```

Pasta, pizza, pepperoni_pizza, and any other folder name will be taken as a label for the program. Images within its parent folder will be labeled as the parent folder’s name. 

If you do not have a dataset, consider looking for one on Kaggle and please also refer to using KaggleHub for downloading the dataset into a directory.

### Uploading to a System

This section demonstrates the steps to uploading the YAML configuration to a system.

1. Navigate to https://portal.expanse.sdsc.edu/ 
2. Under **Files**, click **Home Directory**.

![Expanse Home Directory](./documentation/images/image27.png)

3. Click on **Upload** and here you may upload the configuration you created.

![Upload Configuration](./documentation/images/image23.png)

![Upload Dialog](./documentation/images/image1.png)

![Select File](./documentation/images/image2.png)

![Uploaded Config](./documentation/images/image10.png)

4. The path to your configuration file can be found by clicking the **Copy Path** button, pasting that output, and appending “/{your config name}”.
   - For example: `/home/jseh/expanse/test_config.yaml`
5. Remember/Write down this file path.

——————————————————————————————————————————

### Running the Application

1. Navigate to https://icicleai.tapis.io/ 
   - Under **Tapis Services** click on **Apps**.
   - From the sidebar, scroll down and click on **digital-age-edu**.

![Tapis Apps](./documentation/images/image4.png)

2. Click **Submit Job**. Afterwards click **USE GUIDED JOB LAUNCHER**.

![Submit Job](./documentation/images/image12.png)

![Use Guided Job Launcher](./documentation/images/image20.png)

3. This will pull up the Guided Job Launcher. This will be the main interface we use to start the application. Click **Continue**.

![Guided Job Launcher](./documentation/images/image16.png)

4. This is the **Execution Options** page. These determine the System the program will run on alongside the directory the program will run in.
   - Under **Execution System** select `expanse-tapis`.
   - Under **Batch Logical Queue** select `tapisGPUshared`.
   - Under **Execution System Execution Directory**, **Execution System Input Directory**, and **Execution System Output Directory**, write down the path you want the application to run on. Append a “/${JobUUID}” to the end.
   - Remember/Write this down somewhere. Make sure it is a path on that system and a valid path on your account. For example: `/home/<your_username>/${JobUUID}`.

![Execution Options](./documentation/images/image17.png)

![Queue and Directories](./documentation/images/image18.png)

5. Click **Continue** until you reach **Arguments**. This section includes application arguments. We will be inputting the configuration created earlier. If you didn’t yet do so please refer back to Prerequisites.
   - Inside **Value** paste in the absolute path to the YAML configuration you created, for example mine would be: `/home/jseh/expanse/test_config.yaml`.

![Job Arguments](./documentation/images/image13.png)

6. Click **Continue** until you reach **Scheduler Options**. In this section you define the id of your project to charge for usage. You can find the id here: https://portal.expanse.sdsc.edu/pun/sys/stats 
   - Input `-A {Your Project ID}`.

![Scheduler Options](./documentation/images/image9.png)

7. Click **Continue** until you reach the **Job Submission** page.
   - Click **Submit Job**.
   - Keep note of the job id. In this example it is `d15d50c5-794…….`.
   - Navigate back to the main page and click on **Jobs**.
   - Here you can see the job has been queued into Tapis. It will take some time for the application to run.
   - Please note to see any program text outputs it will be within `tapisjob.out` and you will need to reload the page to see current updates on the job status.

![Job Queued](./documentation/images/image25.png)

![Job Monitoring](./documentation/images/image22.png)

![Job Status and Logs](./documentation/images/image21.png)

——————————————————————————————————————————

### Understanding the Outputs

The application is done running one in Jobs you see this:

![Finished Job Status](./documentation/images/image28.png)

#### Outputs

This section details the outputs of the program, how to use them, and overall expectations for after it runs.

1. **`models/`**
   - A `.pth` with weights to the trained DINOv2 model for classification
   - `sam_vit_b_.pth` weights for segmentation

2. **`{the output directory name defined in the config}/`**
   - `results.json`: Overall metrics for the pipeline and training/inference
   - `class_mapping.json`: Indexes the classes found to a number
   - `confusion_matrix.png`: Confusion matrix compiled from each fold
   - `eval_confusion_matrix.png`: Final model confusion matrix across entire dataset
   - `curriculum.json`: A json file for the curriculum
   - `curriculum_{grade_level}.md`: A markdown variant of the curriculum
   - `cv_report.json`: Model performance per fold
   - `results.csv`: The CSV containing metadata and data for every image

3. **`{the output directory name defined in the config}/exercises:`**
   - **`Week_{xx}/`**
     - **`Module/`**
       - `concepts.md`: markdown containing concepts needed for the given module
       - `{concept}_exercise.py`: The exercise for the student to complete. These are meant to be incomplete when generated so will fail when first ran
       - `{concept}_solution.py`: The solution to the exercise
       - `{concept}_test.py`: The test cases for the student to use
       - `resources.md`: Markdown containing resources for the module

4. **`{the output directory name defined in the config}/images`**
   - `masks/`: The mask used for segmentation
   - `segmented/`: The segmented image

#### Accessing the Outputs

This section goes over how to access and use the outputs from the system.

1. Log into your system at https://portal.expanse.sdsc.edu/ 
2. Click on **expanse Shell Access**.
3. Inside the terminal execute the command:
   ```bash
   cd {the execution directory you saved, replacing ${JobUUID} with the job id}
   ```
   For example mine is:
   ```bash
   cd /home/jseh/scratch/jobs/5ce7ce30-50d0-47d1-91be-220c7e4ea26c-007
   ```
4. Execute `ls`. This will list the subdirectories within that directory.
5. Execute `cd output`. This changes your current directory into output.
6. Execute `cd {what you named the directory}`. Ex: my command is `cd skin_cancer_v1`.
7. Execute `cd exercises`. Here you will see the different modules.
8. For now we will go back to install the requirements. Run `cd ../` to change directory into the parent folder. 
   1. Run `module load cpu/0.21.2a  gcc/13.3.0/t46rsdv`
   2. Run `module load python/3.11.9/je56t6b`
9. Run `python -m venv venv`. This will install the python virtual environment into the directory.
10. After it’s done installing run `source venv/bin/activate`. 
11. Execute `pip install uv`.
12. Execute `uv pip install -r requirements.txt`. This will install all the requirement in parallel.
13. Execute `cd exercises` to get back into the exercises, run `ls`, and cd into a week.
14. You may run `nano {the exercise name}_exercise.py` to edit the contents of that week. Saving the contents, you can run `python {the file name}` to run the code within the file.

![Running Exercises](./documentation/images/image5.png)



