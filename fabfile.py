from fabric.api import task, cd, run, env, prompt, execute, sudo
from fabric.api import open_shell, settings, put, local
import os
import boto.ec2
import time

#
#
# TO DEPLOY THE APPLICATION:
#
#
#       fab run_complete_setup
#       fab create_superuser
#
#
#


# do not check credentials into a public repo, or probably any
#  repo. Instead, the credentials file is kept on the local machine
#  and prior to deployment, it must be moved into the directory
#  containing this fabfile.
import credentials
credentials.set_credentials()

# def create_aws_env():
env.hosts = ['*', ]
env['user'] = 'ubuntu'
# Getting a connection to us-west-2:
env['aws_region'] = 'us-west-2'


def _install_pips(askforchoice=True):
    with cd("django-imagr"):
        # For some reason, python-pip doesn't install correctly
        #  on the free tier AMI. So instead of apt-get, install
        #  it from the source location
        #   sudo("apt-get remove python-pip")
        sudo("wget http://raw.github.com/pypa/pip/master/contrib/get-pip.py")
        sudo("python get-pip.py")

        sudo("pip install -r requirements.txt")


def install_pips(askforchoice=False):
    run_command_on_selected_server(_install_pips, askforchoice=askforchoice)


# also, we need to sudo and bind on Ubuntu to get access to low number ports
# sudo(".....b0000")

# when copying using put(), first param is local machine,
#  second is remote, and third is use_sudo=True

# we will need this string to invoke gunicorn

def _runserver():
    sudo("/etc/init.d/nginx restart")
    with cd("django-imagr/imagr_site"):
        sudo("python manage.py --noinput migrate")
        sudo("python manage.py --noinput collectstatic")
        # CMGTODO: maybe "run" below to avoid overprivileging the app
        run('gunicorn -b 127.0.0.1:8888 imagr_site.wsgi:application')


def runserver(askforchoice=True):
    run_command_on_selected_server(_runserver, askforchoice=askforchoice)


# "Our interactions with boto are all oriented around
# creating and destroying servers.
# In fabric, our orientation will be toward
# manipulating a server once it exists.
# Before we do that, though we need to
# get a server running."
def get_ec2_connection():
    if 'ec2' not in env:
        ec2_connection = boto.ec2.connect_to_region(env.aws_region)
        if ec2_connection is not None:
            env.ec2 = ec2_connection
            print("Connected to EC2 region {}".format(env.aws_region))
        else:
            raise IOError(
                "Unable to connect to EC2 region {}".format(env.aws_region))
    return env.ec2


# "Arguments passed in from the command line appear in your function
# as strings. You are responsible for converting them if needed."
# Fabfile will run the following Python command using your command line args:
# provision_instance(wait_for_running, timeout, interval)
def provision_instance(wait_for_running=False, timeout=60, interval=2):
    wait_value = int(interval)
    timeout_value = int(timeout)
    connection = get_ec2_connection()
    # NOTE: Changing the following value can
    #       cost you money if you aren't careful.
    instance_type = 't1.micro'
    # This one is in your ~/.ssh dir:
    key_name = 'pk-aws'    # key pair name without .PEM suffix
    security_group = 'ssh-access'
    ami_id = 'ami-37501207'

    reservations = connection.run_instances(ami_id,
                                            key_name=key_name,
                                            instance_type=instance_type,
                                            security_groups=[security_group])

    new_instances = []
    for each_instance in reservations.instances:
        if each_instance.state == u'pending':
            new_instances.append(each_instance)
    running_instance = []
    if wait_for_running:
        time_waited = 0
        while new_instances and (time_waited < timeout_value):
            time.sleep(wait_value)
            time_waited += int(wait_value)
            for each_instance in new_instances:  # range!
                current_state = each_instance.state
                print("Instance {} is currently {}".format(each_instance.id,
                                                           current_state))
                if current_state == "running":
                    # NOTE: This part does not work for circumstances where
                    #  len(new_instances) > 1, but that's okay, because this is
                    #  provision_instance, not provision_instances(). It's very
                    #  unpythonic though and must be changed when I have more
                    #  time.
                    running_instance.append(
                        new_instances.pop(new_instances.index(each_instance)))
                each_instance.update()

# Example use of above function:
# fab provision_instance:wait_for_running=1

# Example output:
# [localhost] Executing task 'provision_instance'
# Connected to EC2 region us-west-2
# Instance i-8c424a85 is pending
# Instance i-8c424a85 is pending
# Instance i-8c424a85 is pending
# Instance i-8c424a85 is pending
# Instance i-8c424a85 is pending
# Instance i-8c424a85 is pending
# Instance i-8c424a85 is pending
# Instance i-8c424a85 is running
# Done.

# "Once the function completes, you should be able to load your EC2
# dashboard and see the new instance you just created running happily."


# "When you execute a function using fabric, it is actually run repeatedly,
# once for each host you list in the env.hosts environment setting.
# At the moment, our script lists 'localhost', but we don't actually want
# to run this command on 'localhost', so we need to get around this.
# We could add a new host into the list, but that would require our
# knowing the name of the host ahead of time.
# Moreover, it would still mean that the commands were run both
# on localhost and this new remote host. That's no good."

# "Fabric provides the execute command specifically for this purpose.
# We can pass it the list of hosts on which we want to run a particular
# command, and it will do so for us. This means that we can dynamically
# set the name of the instance we want, and fabric will execute
# our chosen command on that server only!"

# "In order to play with that, though, we need to interactively select the
# instance we want to use (after all, we might have more than one, right?).
# We'll begin by building a function that allows us to list instances,
# optionally filtering for a particular state."

# NOTE: When list_aws_instances is not given :verbose=1, it will not print
#       anything about instances; it is used to prep for another function.
def list_aws_instances(verbose=False, state='all'):
    ec2_connection = get_ec2_connection()
    reservations = ec2_connection.get_all_reservations()
    instances = []
    for each_reservation in reservations:
        for each_instance in each_reservation.instances:
            if state == 'all' or each_instance.state == state:
                each_instance = {
                    'id': each_instance.id,
                    'type': each_instance.instance_type,
                    'image': each_instance.image_id,
                    'state': each_instance.state,
                    'instance': each_instance,
                }
                instances.append(each_instance)  # !
    env.instances = instances
    if verbose:
        import pprint
        pprint.pprint(env.instances)

# Example use of above function:
# fab list_aws_instances:verbose=1,state=running

# Example output:
# [localhost] Executing task 'list_aws_instances'
# Connected to EC2 region us-west-2
# [{'id': u'i-ab5159a2',
#   'image': u'ami-d0d8b8e0',
#   'instance': Instance:i-ab5159a2,
#   'state': u'running',
#   'type': u't1.micro'}]
# Done.


# "Here, we build a list of the available instances that are 'running',
# and then ask the user to choose among them.
def select_instance(state='running', askforchoice=True):
    # If there is no active instance, exit the function:
    if env.get('active_instance', False):
        return

    list_aws_instances(state=state)

    if askforchoice:
        prompt_text = "Please select from the following instances:\n"
        # NOTE: The following syntax does different stuff from {} and .format()
        instance_printing_template = " %(ct)d: %(state)s instance %(id)s\n"

        for idx, instance in enumerate(env.instances):
            ct = idx + 1
            args = {'ct': ct}
            args.update(instance)
            prompt_text += instance_printing_template % args
        prompt_text += "Choose an instance: "

        def validation(input):
            choice = int(input)
            if choice not in range(1, (len(env.instances) + 1)):
                raise ValueError("{} is not a valid instance.".format(choice))
            else:
                return choice

        choice = prompt(prompt_text, validate=validation)
    else:
        choice = 1

    # "After a valid choice is made, we can then hang that instance
    # on our env so that we can access it from other functions:"
    env.active_instance = env.instances[choice - 1]['instance']


def run_command_on_selected_server(command, askforchoice=True):
    # Ask the user to select an instance:
    select_instance(askforchoice=askforchoice)
    # Build a list of hosts, including the server (always ubuntu for us):
    # (This is what Charles and I had a hard time finding due to AWS subnets!)
    selected_hosts = [
        'ubuntu@' + env.active_instance.public_dns_name
    ]
    # Execute the command:
    execute(command, hosts=selected_hosts)


def run_command_on_localhost(command):
    execute(command, host=['localhost', ])


def _copy_credentials_file_locally():
    local("cp ./imagr_site/imagr_site/credentials.py ./")


def _restart_server():
    sudo("shutdown -r now")
    # No sleep is needed because the main chaining function
    #  will perform the wait
    # time.sleep(60)

# "Remember, you cannot use password authentication to log into AWS servers.
# If you find that you are prompted to enter a password in order to run
# this command on your remote server, it means you have some work to do."


# ((Do this first maybe? Review))
# "In order to run a command on this server, you need to ensure that
# the keypair you set up for your AWS instances is available to the ssh agent.
# You can do that at the system level on your local machine:
#       ssh-add ~/.ssh/pk-aws.pem
# Now your local ssh agent knows that this is a file you might use
# to connect. When the AWS server asks to use public-key authentication,
# the agent will then try this key along with any others the agent
# knows about. If no known key works, ssh will bomb out."

def _setup_imagr_aptgets():
    # check for any system updates
    # a wait is necessary here because the server may still be
    # not ready
    time.sleep(90)
    sudo("apt-get -y update")

    # check for any system upgrades
    sudo("apt-get -y upgrade")

    # normally, install python-pip. But this version is bad for
    # the Ubuntu on this particular AMI
    # https://bugs.launchpad.net
    # /ubuntu/+source/python-pip/+bug/1306991/comments/24
    # sudo("apt-get -y install python-pip")
    sudo("apt-get -y install python-dev")
    sudo("apt-get -y install postgresql-9.3")
    sudo("apt-get -y install postgresql-server-dev-9.3")
    sudo("apt-get -y install git")
    sudo("apt-get -y install gunicorn")
    sudo("apt-get -y install nginx")

    # if any updates were performed above, we probably have to reboot server

    sudo("/etc/init.d/nginx start")
    _restart_server()


def setup_imagr_aptgets():
    run_command_on_selected_server(_setup_imagr_aptgets)


def _move_sources():
    # CMGTODO:
    # We don't want to git clone if we already have this directory
    #  set up on the machine.
    run("git clone https://github.com/CharlesGust/django-imagr.git")
    sudo("ln -s " +
         "/home/ubuntu/django-imagr/nginx.conf " +
         "/etc/nginx/sites-enabled/amazonaws.com")

    with cd("django-imagr"):
        put("imagr_site/imagr_site/credentials.py",
            "/home/ubuntu/django-imagr/imagr_site/imagr_site/credentials.py",
            use_sudo=True)


def move_sources():
    run_command_on_selected_server(_move_sources)

# The following two functions are useful if nginx is used to run the
#  server instead of gunicorn
# # An internal command that should be wrapped for fab:
# def _install_nginx():
#     sudo('apt-get install nginx')
#     # This command runs nginx with the start arg:
#     sudo('/etc/init.d/nginx start')


# # "Finally, we need to wrap this function in a function we might call
# # from the command line that will run it on the server we select:""
# def install_nginx():
#     run_command_on_selected_server(_install_nginx)

# "Now, if we run this fabric command from our command line,
# we can get nginx installed on our AWS instance:
#       Executing task 'install_nginx'
#       Connected to EC2 region us-west-2
#       Please select from the following instances:
#        1: running instance i-ab5159a2
#       Choose an instance: 1
#       Executing task '_install_nginx'
#       sudo: apt-get install nginx
#       out: Setting up nginx-full (1.1.19-1ubuntu0.5) ...
#       out: Setting up nginx (1.1.19-1ubuntu0.5) ...
#       out: Processing triggers for libc-bin ...
#       out: ldconfig deferred processing now taking place
#       Done.
# At this point, you should be able to open a web browser and point
# it at your EC2 instance and see the default nginx web page.
# Remember, the public_dns_name of your instance is the way to get at it,
# so use that in your browser:
#       http://ec2-54-185-44-188.us-west-2.compute.amazonaws.com
# Challenge yourself to add two more functions:
#       1. Select a running instance to stop,
#           and then stop it with boto
#       2. Select a stopped instance to terminate,
#           and then terminate it with boto"


def stop_running_instance(askforchoice=True):
    # This code is from:
    #    https://github.com/miracode/django-imagr/blob/master/fabfile.py
    # I tried to find a way to do this using run_command_on_selected_server(),
    # but miracode's example turned out to be the way to go.
    # This is because the various commands store things in fabric's env
    # rather than passing them as parameters, which threw me through a
    # loop at first. Printing the state of the dictionary as things run
    # might help visualize this if your future fabfiles get longer.

    # Have the user place an instance selection in the env:
    select_instance(askforchoice=askforchoice)

    # Acquire a connection. Should done in this instance rather than
    # relying on the fact that select_instance() calls list_aws_instances().
    # It might be technically possible to place a connection in the env,
    # but I'd prefer to keep them function-scoped.
    ec2_connection = get_ec2_connection()

    # This command is too simple to require execute:
    ec2_connection.stop_instances(instance_ids=[env.active_instance.id])


def _terminate_instance(state, askforchoice=True):
    # This code is also derived from:
    #    https://github.com/miracode/django-imagr/blob/master/fabfile.py

    select_instance(state=state, askforchoice=askforchoice)

    ec2_connection = get_ec2_connection()

    ec2_connection.terminate_instances(instance_ids=[env.active_instance.id])


# Similarly to stop_running_instance(), this function will not be
# effectively chained further up than select_instance().
def terminate_stopped_instance(askforchoice=True):
    _terminate_instance("stopped", askforchoice)


def terminate_running_instance(askforchoice=True):
    _terminate_instance("running", askforchoice)


def run_custom_command(command):
    select_instance(askforchoice=False)
    sudo(command)


# The following comes mostly from miracode again. Reference:
# https://github.com/miracode/django-imagr/blob/master/fabfile.py
def _setup_database():
    # Insert the database password into the os.environ dictionary (without
    # make it visible on GitHub, from this file):
    # Turns out this has to be called outside of the fabfile's functions'
    # scope for some reason -- it can't import packages inside functions
    # and I'm not entirely sure why. It might be trying to run the functions
    # somewhere other than the fabfile's directory but on the same machine.
    # More discussion and a record of my failed attempt is saved at the
    # following function's comment:
    # _set_credentials()
    # Take it out of the dictionary and use it for the SQL command string,
    # which is handed to the server instance after it's constructed:
    password = os.environ['DATABASE_PASSWORD']

    sudo('createdb imagr', user='postgres')

    create_user_sql_query = """"
    CREATE USER imagr WITH password '%s';
    GRANT ALL ON DATABASE imagr TO imagr;"
    """ % password

    sudo('psql -U postgres imagr -c %s' % create_user_sql_query,
         user='postgres')


def setup_database(askforchoice=True):
    run_command_on_selected_server(_setup_database, askforchoice=askforchoice)


def _alter_database_user_password():
    password = os.environ['DATABASE_PASSWORD']

    alter_password_sql_command = "ALTER ROLE imagr password to '%s';" % password

    sudo('psql -U postgres imagr -c "%s"' % alter_password_sql_command,
         user='postgres')


def alter_database_user_password():
    run_command_on_selected_server(_alter_database_user_password)


def ssh():
    run_command_on_selected_server(open_shell)


def run_complete_setup():
    provision_instance(wait_for_running=True)
    run_command_on_selected_server(_setup_imagr_aptgets, askforchoice=False)
    # _setup_imagr_aptgets()
    time.sleep(120)

    run_command_on_selected_server(_move_sources, askforchoice=False)
    # _move_sources()

    run_command_on_selected_server(_install_pips, askforchoice=False)
    # install_pips()

    run_command_on_selected_server(_setup_database, askforchoice=False)
    # _setup_database()

    run_command_on_selected_server(_runserver, askforchoice=False)
    # runserver()


# At the time of this writing, the app is now deployable automatically
# using 'fab run_complete_setup' from the fabfile.py directory.

# One problem remains: The django-registration-redux package and its default
# templates include references to a 'site' object, as in {{ site.domain }},
# which was not mentioned anywhere else we've run into while developing
# the project so far.

# This causes it to create emails that redirect newly-registered users to
# the proxy address gunicorn is using to talk to Nginx, which is currently
# 127.0.0.1:8888, which will cause registration emails to direct
# newly-registered users to a nonexistent site on their own machine.

# The fabfile will still start the server on its own, but to make it
# accessible to the outside world it is currently necessary to make
# an admin with the following command, once again with credit to:
# https://github.com/miracode/django-imagr/blob/master/fabfile.py
def _create_superuser():
    with cd('django-imagr/imagr_site'):
        sudo('python manage.py --noinput migrate')
        sudo('python manage.py -noinput createsuperuser')


def create_superuser(askforchoice=False):
    run_command_on_selected_server(_create_superuser,
                                   askforchoice=askforchoice)
