# TreatmentPlanGUI
GUI for creating and modifying treatment plans for different phantom CT sets. 

Functionality includes:
1. Uploading a patient CT set with accompanying treatment plan (all in DICOM format).
2. Visualization of spots within treatment plan, with ability to to cycle through each layer/energy.
3. Ability to upload a new treatment plan in .csv format.
4. Ability to select a new CT set to associate with the new plan.
5. Able to change gantry angle, isocenter, and include set-up beam.
6. Creates treatment plan based off all inputs and selected parameters.
7. Finally, uploads the new plans to the PACS server so that they are immeidately available to load. 
