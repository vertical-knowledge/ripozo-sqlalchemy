1.0.2 (2016-03-29)
==================

- Pagination now automatically converts strings to integers for the page and count


1.0.1 (2015-12-01)
==================

- Easy resources updated to use create_fields, update_fields, and list_fields options.
- append_slash option added to easy resources
- Simplified mechanism of getting relationships to avoid private variables


1.0.0 (2015-06-30)
==================

- Added _COLUMN_FIELD_MAP for determining python type.  Transparent change.


1.0.0b1 (2015-06-29)
====================

- Fixed bug in retrieve_list with improperly named link to previous ("prev" --> "previous")
- Removed all fields flag.
- Renamed alcehmymanager to alchemymanager
- easy resources added.  By simply calling create_resource with a session_handler and sqlalchemy model, you can automatically create a full resource. and immediately add it to a dispatcher.


0.2.0 (2015-06-08)
==================

- Tests fixed.


0.2.0b1 (2015-06-05)
====================

- Breaking Change: You are now required to inject a session handler on instantiation of the manager.


0.1.6b1 (2015-06-04)
====================

- Sessions are only grabbed once in any given method.  This allows you to safely return a new session every time
- Added a method for after a CRUD statement has been called.


0.1.5 (2015-04-28)
==================

- Optimization for retrieving lists using ``AlchemyManager.list_fields`` property for retrieving lists
- Retrieve list now properly applies filters.
- meta links updated in retrieve_list.  They now are contained in the links dictionary
- previous linked rename to prev in retrieve_list meta information


0.1.4 (2015-03-26)
==================

- Nothing changed yet.


0.1.3 (2015-03-26)
==================

- Nothing changed yet.


0.1.2 (2015-03-24)
==================

- NotFoundException raised when retrieve is called and no model is found.


0.1.1 (2015-03-15)
==================

- Added convience attribute for using all of the columns on the model.