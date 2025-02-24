import subprocess
from framework import constants, settings
import logging
import os

logger = logging.getLogger(__name__)


class OcOutput(list):
    """
    Class takes a list of output (table kubectl output)
        and converts it to a dictionary to read columns easier
    Example:
        ["NAME","STATUS","queue_service_pod","Running"] - >
        {
            "name":"queue_service_pod",
            "status":"running"
        }
    Validations:
        List length is even, if not, something in the received list is wrong
    """

    def as_dict(self) -> dict:
        l = len(self) / 2
        l = int(l) if l.is_integer() and l != 0 else None
        if l:
            keys = map(
                str.lower, self[:l]
            )  # Better to have lower char keys, more pythonic
            values = map(
                str.lower, self[l:]
            )  # Better to have lower char keys, more pythonic
            return dict(zip(keys, values))
        else:
            return {}


class DjangoPod:
    def __init__(self, name=None):
        self.name = name or self.get_first_pod_from_deployment()
        self.__django_superuser = None

    def get_first_pod_from_deployment(self):
        django_pod_name_command = f"oc get pods -n {settings.get('NAMESPACE')} -l {constants.LABEL_STR_DJANGO} -o=jsonpath={{@.items[0].metadata.name}}"
        pod_name = (
            exec_cmd(django_pod_name_command)[1]
            .rstrip()
        )
        return pod_name

    def migrate_db(self):
        migrate_db_cmd = f"oc exec -n {settings.get('NAMESPACE')} {self.name} -- python manage.py migrate"
        run_migrate_db = (
            exec_cmd(migrate_db_cmd)[1].rstrip()[1]
        )

        # TODO: REPLACE TO LOGGER:
        print(run_migrate_db)

        return None

    def create_or_get_super_user(self):
        try:
            superuser_cmd = f"oc exec -n {settings.get('NAMESPACE')} {self.name} -- python manage.py createsuperuser --noinput"
            run_create_super_user = (
                exec_cmd(superuser_cmd)[1]
                .rstrip()
            )

            # TODO: REPLACE TO LOGGER:
            print(run_create_super_user)

            return None
        except Exception:
            logger.warning(
                msg="Skipping superuser creation, user might be already existing!"
            )

        finally:
            # TODO GET THE SUPERUSER USER DYNAMICALLY AND NOT HARDCODE:
            self.__django_superuser = "admin"

    def get_superuser_token(self):
        get_user_token_cmd = f"oc exec -n {settings.get('NAMESPACE')} {self.name} -- python manage.py retrieve_token -u {self.__django_superuser}"
        run_get_user_token = (
            exec_cmd(get_user_token_cmd)[1]
            .rstrip()
        )

        return run_get_user_token


def exec_cmd(cmd, **kwargs):
    """
    Run command
    """
    print(f"Executing command: '{cmd}'")
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        shell=True,
        **kwargs,
    )
    stdout = result.stdout.decode("utf-8")
    stderr = result.stderr.decode("utf-8")
    rc = result.returncode
    print(f"rc: {rc}")
    print(f"stdout: '{stdout}'")
    print(f"stderr: '{stderr}'")
    print()
    return rc, stdout, stderr
