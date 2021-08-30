# Zenkly

Over the years, I’ve written many scripts to read/edit data from Zendesk. Some of those scripts were used over and over again. To make those scripts more accessible to others who may also want to use them, I’ve created a CLI called Zenkly (_Zendesk + CLI_).

## Installation

### Prerequisites

In order to install and use Zenkly, you’ll need to have Python 3 installed on your computer. You can follow [these instructions](https://realpython.com/installing-python/) to ensure you have the latest version of Python installed. _Note: Zenkly is only compatible with Python 3._

You can verify that you have the correct version of Python installed by running the following command in your terminal:

`python3 --version`

You should see the latest version of Python printed out (at time of writing, 3.9.6).

#### Installing using PIP (recommended)

You can install Zenkly using PIP with the following command:

`python3 -m pip install zenkly`

Once the installation finishes, confirm that everything is working by running:

`zenkly --help`

You should see all the available Zenkly commands printed out.

## Configuring Zenkly

The first time you use Zenkly, you’ll need to configure it to use your Zendesk credentials. To do this, run the following command:

`zenkly configure`

You will be prompted to enter your Zendesk subdomain, email address, and password. If you are using an API token to authenticate (instead of a password), enter your credentials as follows:

```
Email: youremail@gmail.com/token
Password: [your API token]
```

If you’ve already configured Zenkly, but would like to set up a second configuration (to work with two different Zendesk instances, for example), you can run the following:

`zenkly --profile [profile_name] configure`

This will set up a new configuration with the chosen profile name. Future commands can then be run with the `--profile` option to select which configuration to use. For example:

`zenkly --profile [profile_name] get-macros`

The default configuration is saved with the profile name `default`. You do not need to use the `--profile` option when running commands with the `default` configuration.

## Commands

Zenkly currently supports the following commands:

Command Name | Description
-- | --
`add-macros` | Create macros from file.
`backup-guide` | Backup Guide categories, sections and articles.
`configure` | Configure Zendesk authentication.
`create-article-mapping` | Generate a JSON object with mapping based on provided backup files.
`get-automations` | Get all automations and save to file.
`get-macros` | Get all macros and save to file.
`get-triggers` | Get all triggers and save to file.
`get-views` | Get all automations and save to file.
`show-brands` | Show brands as tabular data.
`updates-macros` | Update all macros from file.
`upload-theme` | Upload help center theme zip file.

You can learn more about each command, including which options it supports, by using the `--help` flag.

## Bug Reports / Contributing

Bug reports can be submitted [here](https://github.com/zenahirsch/zenkly/issues). Pull requests are also welcome.
