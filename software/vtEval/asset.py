import inspect, pkg_resources

def locateAsset(*resourceParts):
	resource = '/'.join(['assets'] + list(resourceParts))
	callingFrame = inspect.stack()[1]
	callingModule = inspect.getmodule(callingFrame[0])

	return pkg_resources.resource_filename(callingModule.__name__, resource)
