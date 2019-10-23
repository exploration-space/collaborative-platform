import hashlib

from django.contrib.auth.models import User
from django.db import models
from django.db.models import QuerySet
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.http import HttpResponse

from apps.projects.models import Project

UPLOADED_FILES_PATH = 'uploaded_files/'


class FileNode(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    class Meta:
        abstract = True

    def move_to(self, directory_id):  # type: (FileNode, int) -> FileNode
        self.parent_dir_id = directory_id
        self.save()
        return self

    def get_path(self):
        s = self
        r = [self.name]
        while s.parent_dir is not None:
            r.insert(0, s.parent_dir.name)
            s = s.parent_dir

        return '/'.join(r)


class Directory(FileNode):
    parent_dir = models.ForeignKey("Directory", related_name='subdirs', on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        unique_together = ("parent_dir", "name")

    def create_subdirectory(self, name, user):  # type: (Directory, str, User) -> Directory
        from apps.projects.helpers import log_activity

        d = Directory(name=name, project=self.project, parent_dir=self)
        d.save()
        log_activity(project=d.project, user=user, related_dir=d,
                     action_text="created directory {} in {}".format(d.name, self.name))
        return d

    def rename(self, new_name, user):  # type: (Directory, str, User) -> Directory
        from apps.projects.helpers import log_activity
        old_name = self.name
        self.name = new_name
        self.save()
        log_activity(project=self.project, user=user, related_dir=self,
                     action_text="renamed directory {} to {}".format(old_name, new_name))

    def get_files(self):  # type: (Directory) -> QuerySet
        return self.files.values()

    def get_subdirectories(self):  # type: (Directory) -> QuerySet
        return self.subdirs.values()

    def get_content(self):  # type: (Directory) -> list
        return list(self.subdirs.order_by('name').values()) + list(self.files.order_by('name').values())

    def move_to(self, directory_id):  # type: (FileNode, int) -> FileNode
        if self.parent_dir_id is None:
            raise ReferenceError("Cannot move parent dir!")

        from apps.files_management.helpers import is_child
        if is_child(self.id, directory_id):
            raise ReferenceError("Moving parent dir to child dir is not allowed.")
        return super().move_to(directory_id)


class File(FileNode):
    version_number = models.PositiveIntegerField()
    parent_dir = models.ForeignKey("Directory", related_name='files', on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        unique_together = ("parent_dir", "name")

    def rename(self, new_name, user):  # type: (File, str, User) -> File
        from apps.files_management.helpers import uploaded_file_object_from_string
        from apps.projects.helpers import log_activity

        old_name = self.name
        if old_name == new_name:
            return

        current_version = self.versions.filter(number=self.version_number).get()
        contents = current_version.get_content()

        hashed = bytes(new_name, encoding='utf8') + \
                 bytes(str(self.project_id), encoding='utf8') + \
                 bytes(str(self.parent_dir_id), encoding='utf8') + \
                 bytes(contents, encoding='utf-8')
        hash = hashlib.sha512(hashed).hexdigest()

        uf = uploaded_file_object_from_string(contents, hash)
        fv = FileVersion(upload=uf, hash=hash, file=self, number=current_version.number + 1, created_by=user)
        fv.save()

        self.version_number += 1
        self.name = new_name
        self.save()
        log_activity(project=self.project, user=user, file=self,
                     action_text="renamed {} to".format(old_name))

    def download(self):
        fv = self.versions.filter(number=self.version_number).get()
        return fv.download()

    def delete(self, using=None, keep_parents=False):
        from apps.files_management.helpers import delete_es_docs
        delete_es_docs(self.id)
        super().delete()

    def get_relative_path(self):
        path = self.name
        parent_dir = self.parent_dir

        while parent_dir is not None:
            path = parent_dir.name + '/' + path
            parent_dir = parent_dir.parent_dir

        return path


class FileVersion(models.Model):
    upload = models.FileField(upload_to=UPLOADED_FILES_PATH)
    hash = models.CharField(max_length=128)
    file = models.ForeignKey(File, related_name='versions', on_delete=models.CASCADE)
    number = models.PositiveIntegerField()
    creation_date = models.DateTimeField(auto_now_add=False)
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='created_fileversions', null=True,
                                   blank=True)

    class Meta:
        unique_together = ("file", "number")

    def get_content(self):
        self.upload.open(mode='r')
        content = self.upload.read()
        self.upload.close()
        return content

    def download(self):
        content = self.get_content()
        response = HttpResponse(content, content_type='application/xml')
        response['Content-Disposition'] = bytes('attachment; filename="{}"'.format(self.file.name), 'utf-8')
        return response
