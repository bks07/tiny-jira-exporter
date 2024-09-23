# Tiny Jira Exporter
This simple Python tool exports data from Jira for further processing.
You can use it to generate a CSV file where each row represents a single JIRA issue.

You can specify which issues it should fetch by using different filter criteria or providing a proper name for a filter that exists and is reachable inside your Jira instance. You can also define attributes the tool returns for each extracted Jira issue. However, the tool's unique feature is that it allows you to extract timestamps based on the transitions of the given issues, allowing you to analyze the cycle times of your issues.

I had the idea to develop this tool since I used the Jira-to-Analytics tool from Daniel S. Vacanti (ActionableAgile(TM), https://github.com/ActionableAgile/jira-to-analytics). Since 2017, I have used this tool to export Jira data or analyze cycle times.
Since I am using my own Jira Cloud instance, I got frustrated because the Jira-Analytics didn't seem to work properly with Jira Cloud. I was also missing some other features, so I decided to write my own tool.

The Tiny Jira Exporter uses the basic ideas of the Jira-to-Analytics tool, such as configuring via a YAML file or creating the output into a CSV file.
However, I developed this tool from scratch since Jira-to-Analytics is written in TypeScript - for which I have no experience. Thus, I developed this tool in Python.
The usage of my tool is also slightly different, and I will continue to add features. Since it is open for contribution, contact me via LinkedIn to join my GitHub project if interested.

# Installation
## Using the .EXE file
When you mare a Windows user, just download the latest EXE file from the releases and that's it.

## Using the Python script
Install at least Python 3.10.12 and pip.
Clone this repository and install all required modules as specified in the file _requirements.txt__.
```bash
$ pip install -r requirements.txt
```

# Usage
## EXE file under Windows
When using the EXE file the command should look like this.
```bash
> .\TinyJiraExporter.exe -c ./conf/my-config.yaml -o ./export/my-output.csv
```
## Python Script
Call the Python script using the following code.
```bash
$ python3 jira-to-analytics.py -c ./conf/my-config.yaml -o ./export/my-output.csv
```

## Parameters
Provide the following parameters:
* -c - Stands for _configuration_ and must be followed by the path to the configuration YAML file you want to use. If you are not specifying this parameter, the script will use the _default.yaml_ file inside the folder _conf_.
* -o - Stands for _output_ and must be followed by the path to the file you want to write the CSV data. If you are not specifying this parameter, the script will use the _default.csv_ csv file inside the folder _export_.
Ensure that the paths are valid and that the config file exists. Any further configuration is done inside the YAML file.

# Configuration
The best start to configure your export is to copy the file _default.yaml_, rename the copied file and change its contents to your needs.
I will describe the sections of the YAML configuration file in the following. Please note that whenever there are new features in the script, the configuration file may change as well. However, I try to ensure backward compatibility.

## Connection
Specify your domain, username and API token to grant access to your Jira instance. Read [Atlassian's tutorial](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/) how to set up and use API tokens.
Leaving these values empty, commenting them out or removing them from the file results in a prompt where you must enter the missing values after you started the script.

## Search Criteria
This section allows you to use a predefined filter or to set up a simple filter by providing some values.
I always recommend setting up a proper filter inside Jira. If a filter exists, use the exact name inside the YAML file. However, make sure that the user you are connection with the script has the proper rights to access the filter.

If you don't want to use a Jira filter, comment out the attribute _"Filter"_. Then, you must set proper values to _"Projects"_, _"Issue Types"_, and the dates for exclusion.

## Mandatory
__Important:__ Always check the values in this section. It is important that these values are properly set! Follow the instructions in the comments of the YAML file.

## Default Issue Fields
Please note that the script always exports the issue key and the issue ID.
Currently, the script supports to export the following standard issue fields.
* Reporter
* Assignee
* Summary
* Status
* Resolution
* Priority
* Created
* Updated
* Resolved
* Parent
* Flagged
* Labels

For disabling the export of a given field, you can delete the lines, you can comment them out, or set them to No. The least is the recommended method.
```yaml
Standard Issue Fields:
    Reporter: !!bool Yes # will be exported
    Assignee: !!bool No # not included in export
#    Summary: !!bool Yes # not included in export
```
The example above only exports the field _Reporter_.

## Custom Issue Fields
```yaml
Custom Issue Fields:
    story-point-estimates: customfield_10016
```
Please check the correct IDs like _customfield\_xxxxx_. Inside Jira, navigate to _"Cog item > Issues > Custom Fields"_. Search for the custom field you are interested in. Then, click on the three dots at the very right in the row of the custom field and select _"View field information"_. When opening the field information, you can see the ID in the address line of your browser after "customFieldId=". For instance:

```javascript
https://YOUR-NAME.atlassian.net/secure/admin/ConfigureCustomField!default.jspa?customFieldId=10045
```
The ID in this example is 10045. It should result in the following configuration entry.
```yaml
Custom Issue Fields:
    my-custom-field: customfield_10045
```

You can leave it empty if you don't want to extract any custom fields at all.

__Important:__ I hightly recommend to only use lower-case characters and the dash symbol for naming the custom fields. The script will not extract two issue fields with the same name.


### Flagged
Flagged is listed as a custom field, however, the exporter handles it as a default issue field. The reason is, that the flagged field holds an object that has to be further processed. Therefore, it requires a special treatment by the exporter.

### Story Points
If you want to export story points, always search for the custom field 'Story points estimate'. The custom field "Story Points" is a legacy field that is not used by modern Jira Cloud.


## Workflow
Define a workflow that is used for extracting dates that can be used for, e. g., estimating cycle times. It is important that you must map the statusses of your workflow to categories.
Whenever a Jira issue entered one status of a given category, the algorithm of this script saves the date when it happened.
When you have moved issues backwards from one category to another, the script will delete the timestamp for the categories that come after the new category. This ensures a Kanban-compliant analysis.

The following workflow mapping is the most simple example.
```yaml
Workflow:
    to-do: # A category for the given status
        - To Do # A status as defined inside Jira
    doing: # Categoriy
        - Doing # Status
    done: # Category
        - Done # Status
```

However, the original idea of the categories is that you can map multiple status to one category.
```yaml
Workflow:
    backlog: # A category for the given status
        - To Do # A status as defined inside Jira
        - Open
    in-progress:
        - In Progress
    done:
        - Done
        - Closed
```

## Misc
I recommend leaving it as it is. However, all of the values are optional here. You may change it or comment them out, if you like.

# Support
This script is maintained by [Boris Karl Schlein](https://github.com/bks07).

You may also be interested in the following articles that make use of this script:
* [Easy Risk Management with Jira, Confluence, and Excel](https://medium.com/agileinsider/easy-risk-management-with-jira-confluence-and-excel-c7b2dd13f848)