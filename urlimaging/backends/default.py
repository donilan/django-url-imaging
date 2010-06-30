import os, shutil, time
from django.conf import settings

from boto.s3.connection import S3Connection
from boto.s3.key import Key, S3DataError


# XXX move into __init.py__
conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
bucket = conn.get_bucket(settings.S3_BUCKET)

class ImageStorage:
	def delete_image(self, hash):
		raise Exception('delete_file not implemented')

	def save_image(self, filename):
		raise Exception('save_image not implemented')

	def get_image_url(self, hash):
		raise Exception('get_image_url not implemented')


def retry(times, ex):
	""" A decorator which can be called as:

		@retry(5, S3DataError)
		def fn():
			pass

	    and will call fn and if it throws an exception, it will keep
	    trying 5 times. """
	def retry_wrap(fn):
		def fn_wrap(*args, **kwargs):
			for i in range(times-1):
				try:
					return fn(*args, **kwargs)
				except ex:
					pass
			return fn(*args, **kwargs)
		return fn_wrap
	return retry_wrap


class S3ImageStorage(ImageStorage):
	def delete_image(self, hash):
		k = Key(bucket, hash)
		k.delete()
		k.close()

	@retry(3, S3DataError)
	def save_image(self, hash, filename):
		key = Key(bucket, hash)
		key.set_contents_from_filename(filename, 
				{'Cache-Control': 'public, max-age=7200',
				'Expires': time.asctime(time.gmtime(time.time() + 7200)) })
		key.close()

	def get_image_url(self, hash):
		key = Key(bucket, hash)

		ret = key.generate_url(settings.S3_EXPIRES, 'GET', 
				{'Cache-Control': 'public, max-age=7200',
				'Expires': time.asctime(time.gmtime(time.time() + 7200)) })
		key.close()

		return ret


class LocalImageStorage(ImageStorage):
	def delete_image(self, hash):
		# XXX default this to MEDIA_ROOT
		os.unlink(os.path.join(settings.IMAGE_STORAGE_DIR, hash))

	def save_image(self, hash, filename):
		shutil.copyfile(filename, os.path.join(settings.IMAGE_STORAGE_DIR, hash))

	def get_image_url(self, hash):
		return settings.MEDIA_URL + "/" + hash
