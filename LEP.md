# LeaguePredictor Improvement Path
This document is a record of the planed improvements to this package. It is meant to be an intorductory tool to tracking the goals and aspirations of the project until (if) the project becomes too large to track the goals and changes from within the same repo.

Please feel free to add ideas or commentary to the improvement ideas listed below.

## Improvement Path
There are several areas of improvement to this code base that we hope to plan for and prioritize, including,
* Formatting/Code Style
* Model Improvement
* Model Extention

Within each of these areas are sub tasks that can be taken on by contributors to the codebase. It will be up to
the user's interest and the priority of the task as to which tasks get done, when.

### Formatting/Code Style
The initial author of this module is relatively junior and so is using this as a learning opportunity. With that in mind, there are several areas of improvement that can be made to the code structure and quality. Some initial changes that should be implemented (in no particular order) are:
* ~~Turning this module into a package~~ and making it availabel on [pypi](https://pypi.org/)
* Remove magic numbers
* General formatting and readability improvements
* Adding testing
* Run a rudimentary CI/CD pipeline with nox on each push
* Adding Sonar or other code linting/scoring programs
* Making API calls into Async

### Model improvement
* Expand data volume to improve model prediction quality
* Extend data storage type to enable faster processing
* Ways to store the model at the end of training to enable long lived models with prediction comparability
* Establish robust means of making train/test splits in data
* Create metrics to mechanically judge model performance
* Enable dynamic sizing of DNN to minimize CPU and memory while maintaining high performance
* Add recursive data gathering from a seed PUUID as the new end-point to get PUUID from name and tag is hard to get data for



### Model Extention
* Enabling the model to train on roles in addition to team data
* Enable the model to train on player/character data
* Enable the model the use real time data/visual data
