##############################################################################
### DATA FRAME CLASS
##############################################################################

import numpy as np
from . import sc_utils as ut # Note, sc_fileio is also used, but is only imported when required to avoid a circular import
from . import sc_math as mh
from .sc_odict import odict

__all__ = ['dataframe']

class dataframe(object):
    '''
    A simple data frame, based on simple lists, for simply storing simple data.
    
    Example usage:
        a = dataframe(cols=['x','y'],data=[[1238,2],[384,5],[666,7]]) # Create data frame
        print(a)['x'] # Print out a column
        print(a)[0] # Print out a row
        print(a)['x',0] # Print out an element
        a[0] = [123,6]; print(a) # Set values for a whole row
        a['y'] = [8,5,0]; print(a) # Set values for a whole column
        a['z'] = [14,14,14]; print(a) # Add new column
        a.addcol('z', [14,14,14]); print(a) # Alternate way to add new column
        a.rmcol('z'); print(a) # Remove a column
        a.pop(1); print(a) # Remove a row
        a.append([555,2,14]); print(a) # Append a new row
        a.insert(1,[555,2,14]); print(a) # Insert a new row
        a.sort(); print(a) # Sort by the first column
        a.sort('y'); print(a) # Sort by the second column
        a.addrow([555,2,14]); print(a) # Replace the previous row and sort
        a.getrow(1) # Return the row starting with value '1'
        a.rmrow(); print(a) # Remove last row
        a.rmrow(1238); print(a) # Remove the row starting with element '3'
    
    Works for both numeric and non-numeric data.
    
    Version: 2018oct20
    '''

    def __init__(self, cols=None, data=None):
        self.cols = None
        self.data = None
        self.make(cols=cols, data=data)
        return None
    
    def __repr__(self, spacing=2):
        ''' spacing = space between columns '''
        if not self.cols: # No keys, give up
            return '<empty dataframe>'
        
        else: # Go for it
            outputlist = odict()
            outputformats = odict()
            
            # Gather data
            nrows = self.nrows
            for c,col in enumerate(self.cols):
                outputlist[col] = list()
                maxlen = len(col) # Start with length of column name
                if nrows:
                    for val in self.data[:,c]:
                        output = ut.flexstr(val)
                        maxlen = max(maxlen, len(output))
                        outputlist[col].append(output)
                outputformats[col] = '%'+'%i'%(maxlen+spacing)+'s'
            
            ndigits = (np.floor(np.log10(max(1,nrows)))+1) # Don't allow 0 rows
            indformat = '%%%is' % ndigits # Choose the right number of digits to print
            
            # Assemble output
            output = indformat % '' # Empty column for index
            for col in self.cols: # Print out header
                output += outputformats[col] % col
            output += '\n'
            
            for ind in range(nrows): # Loop over rows to print out
                output += indformat % ut.flexstr(ind)
                for col in self.cols: # Print out data
                    output += outputformats[col] % outputlist[col][ind]
                if ind<nrows-1: output += '\n'
            
            return output
    
    def _val2row(self, value=None):
        ''' Convert a list, array, or dictionary to the right format for appending to a dataframe '''
        if isinstance(value, dict):
            output = np.zeros(self.ncols, dtype=object)
            for c,col in enumerate(self.cols):
                try: 
                    output[c] = value[col]
                except: 
                    errormsg = 'Entry for column %s not found; keys you supplied are: %s' % (col, value.keys())
                    raise Exception(errormsg)
            output = np.array(output, dtype=object)
        elif value is None:
            output = np.empty(self.ncols,dtype=object)
        else: # Not sure what it is, just make it an array
            if len(value)==self.ncols:
                output = np.array(value, dtype=object)
            else:
                errormsg = 'Row has wrong length (%s supplied, %s expected)' % (len(value), self.ncols)
                raise Exception(errormsg)
        return output
    
    def _sanitizecol(self, col, die=True):
        ''' Take None or a string and return the index of the column '''
        if col is None:
            output = 0 # If not supplied, assume first column is control
        elif ut.isstring(col):
            try:
                output = self.cols.index(col) # Convert to index
            except Exception as E:
                errormsg = 'Could not get index of column "%s"; columns are:\n%s\n%s' % (col, '\n'.join(self.cols), str(E))
                if die: 
                    raise Exception(errormsg)
                else:
                    print(errormsg)
                    output = None
        elif ut.isnumber(col):
            output = col
        else:
            errormsg = 'Unrecognized column/column type "%s" %s' % (col, type(col))
            if die:
                raise Exception(errormsg)
            else:
                print(errormsg)
                output = None
        return output
    
    def __getitem__(self, key=None, die=True):
        ''' Simple method for returning; see self.get() for a version based on col and row '''
        if ut.isstring(key):
            colindex = self.cols.index(key)
            output = self.data[:,colindex]
        elif ut.isnumber(key):
            rowindex = int(key)
            output = self.data[rowindex,:]
        elif isinstance(key, tuple):
            colindex = self.cols.index(key[0])
            rowindex = int(key[1])
            output = self.data[rowindex,colindex]
        elif isinstance(key, slice):
            rowslice = key
            slicedata = self.data[rowslice,:]
            output = dataframe(cols=self.cols, data=slicedata)
        else:
            errormsg = 'Unrecognized dataframe key "%s"' % key
            if die:
                raise Exception(errormsg)
            else:
                print(errormsg)
                output = None
        return output
        
    def __setitem__(self, key, value=None):
        if value is None:
            value = np.zeros(self.nrows, dtype=object)
        if ut.isstring(key): # Add column
            if not ut.isiterable(value):
                value = ut.promotetolist(value)
            if len(value) != self.nrows:
                if len(value) == 1:
                    value = [value]*self.nrows # Get it the right length
                else:
                    if self.ncols==0:
                        self.data = np.zeros((len(value),0), dtype=object) # Prepare data for writing
                    else:
                        errormsg = 'Cannot add column %s with value %s: incorrect length (%s vs. %s)' % (key, value, len(value), self.nrows)
                        raise Exception(errormsg)
            try:
                colindex = self.cols.index(key)
                val_arr = np.reshape(value, (len(value),))
                self.data[:,colindex] = val_arr
            except:
                self.cols.append(key)
                colindex = self.cols.index(key)
                val_arr = np.reshape(value, (len(value),1))
                self.data = np.hstack((self.data, np.array(val_arr, dtype=object)))
        elif ut.isnumber(key):
            value = self._val2row(value) # Make sure it's in the correct format
            if len(value) != self.ncols: 
                errormsg = 'Vector has incorrect length (%i vs. %i)' % (len(value), self.ncols)
                raise Exception(errormsg)
            rowindex = int(key)
            try:
                self.data[rowindex,:] = value
            except:
                self.data = np.vstack((self.data, np.array(value, dtype=object)))
        elif isinstance(key, tuple):
            try:
                colindex = self.cols.index(key[0])
                rowindex = int(key[1])
                self.data[rowindex,colindex] = value
            except:
                errormsg = 'Could not insert element (%s,%s) in dataframe of shape %' % (key[0], key[1], self.data.shape)
                raise Exception(errormsg)
        return None
    
    
    def __copy__(self, *args, **kwargs):
        ''' Warning, there is a bug in Numpy such that deepcopy(array) != array if array contains lists '''
        newcols = ut.dcp(self.cols)
        listdata = self.data.tolist()
        copied = ut.dcp(listdata)
        newdata = np.array(copied, dtype=object)
        return dataframe(cols=newcols, data=newdata)
    
    
    def __deepcopy__(self, *args, **kwargs):
        ''' As above '''
        return self.__copy__(*args, **kwargs)
    
    
    def __eq__(self, other):
        ''' If columns and data match, the dataframes match '''
        if not isinstance(other, dataframe): return False
        if  self.cols != other.cols:         return False
        if (self.data != other.data).any():  return False
        return True
    
    
    def make(self, cols=None, data=None):
        '''
        Creates a dataframe from the supplied input data. Usage examples:
            df = sc.dataframe()
            df = sc.dataframe(['a','b','c'])
            df = sc.dataframe([['a','b','c'],[1,2,3],[4,5,6]])
            df = sc.dataframe(['a','b','c'], [[1,2,3],[4,5,6]])
            df = sc.dataframe(cols=['a','b','c'], data=[[1,2,3],[4,5,6]])
        '''
        
        # Handle columns
        if cols is None and data is None:
            cols = list()
            data = np.zeros((0,len(cols)), dtype=object) # Object allows more than just numbers to be stored
        elif cols is None and data is not None: # Shouldn't happen, but if it does, swap inputs
            cols = data
            data = None
        if not ut.checktype(cols, 'listlike'):
            errormsg = 'Inputs to dataframe must be list, tuple, or array, not %s' % (type(cols))
            raise Exception(errormsg)
        
        # Handle data
        if data is None:
            if np.ndim(cols)==2 and np.shape(cols)[0]>1: # It's a 2D array with more than one row: treat first as header
                data = ut.dcp(cols[1:])
                cols = ut.dcp(cols[0])
            else:
                data = np.zeros((0,len(cols)), dtype=object) # Just use default
        data = np.array(data, dtype=object)
        if data.ndim != 2:
            if data.ndim == 1:
                if len(cols)==1:
                    data = np.reshape(data, (len(data),1))
                else:
                    errormsg = 'Dimension of data can only be 1 if there is 1 column, not %s' % len(cols)
                    raise Exception(errormsg)
            else:
                errormsg = 'Dimension of data must be 1 or 2, not %s' % data.ndim
                raise Exception(errormsg)
        if data.shape[1]==len(cols):
            pass
        elif data.shape[0]==len(cols):
            data = data.transpose()
        else:
            errormsg = 'Number of columns (%s) does not match array shape (%s)' % (len(cols), data.shape)
            raise Exception(errormsg)
        
        # Store it        
        self.cols = list(cols)
        self.data = data
        return None
    
    
    def get(self, cols=None, rows=None):
        '''
        More complicated way of getting data from a dataframe; example:
        df = dataframe(cols=['x','y','z'],data=[[1238,2,-1],[384,5,-2],[666,7,-3]]) # Create data frame
        df.get(cols=['x','z'], rows=[0,2])
        '''
        if cols is None:
            colindices = Ellipsis
        else:
            colindices = []
            for col in ut.promotetolist(cols):
                colindices.append(self._sanitizecol(col))
        if rows is None:
            rowindices = Ellipsis
        else:
            rowindices = rows
        
        output = self.data[:,colindices][rowindices,:] # Split up so can handle non-consecutive entries in either
        if output.size == 1: output = output[0] # If it's a single element, return the value rather than the array
        return output
   
    def pop(self, key, returnval=True):
        ''' Remove a row from the data frame '''
        rowindex = int(key)
        thisrow = self.data[rowindex,:]
        self.data = np.vstack((self.data[:rowindex,:], self.data[rowindex+1:,:]))
        if returnval: return thisrow
        else:         return None
    
    
    def append(self, value):
        ''' Add a row to the end of the data frame '''
        value = self._val2row(value) # Make sure it's in the correct format
        self.data = np.vstack((self.data, np.array(value, dtype=object)))
        return None
    
    
    @property
    def ncols(self):
        ''' Get the number of columns in the data frame '''
        ncols = len(self.cols)
        ncols2 = self.data.shape[1]
        if ncols != ncols2:
            errormsg = 'Dataframe corrupted: %s columns specified but %s in data' % (ncols, ncols2)
            raise Exception(errormsg)
        return ncols


    @property
    def nrows(self):
        ''' Get the number of rows in the data frame '''
        try:    return self.data.shape[0]
        except: return 0 # If it didn't work, probably because it's empty
    
    
    @property
    def shape(self):
        ''' Equivalent to the shape of the data array, minus the headers '''
        return (self.nrows, self.ncols)
    
    def addcol(self, key=None, value=None):
        ''' Add a new column to the data frame -- for consistency only '''
        self.__setitem__(key, value)
    
    def rmcol(self, key, die=True):
        ''' Remove a column or columns from the data frame '''
        cols = ut.promotetolist(key)
        for col in cols:
            if col not in self.cols:
                errormsg = 'Dataframe: cannot remove column %s: columns are:\n%s' % (col, '\n'.join(self.cols))
                if die: raise Exception(errormsg)
                else:   print(errormsg)
            else:
                colindex = self.cols.index(col)
                self.cols.pop(colindex) # Remove from list of columns
                self.data = np.hstack((self.data[:,:colindex], self.data[:,colindex+1:])) # Remove from data
        return None
    
    def addrow(self, value=None, overwrite=True, col=None, reverse=False):
        ''' Like append, but removes duplicates in the first column and resorts '''
        value = self._val2row(value) # Make sure it's in the correct format
        col   = self._sanitizecol(col)
        index = self._rowindex(key=value[col], col=col, die=False) # Return None if not found
        if index is None or not overwrite: self.append(value)
        else: self.data[index,:] = value # If it exists already, just replace it
        self.sort(col=col, reverse=reverse) # Sort
        return None
    
    def _rowindex(self, key=None, col=None, die=False):
        ''' Get the sanitized row index for a given key and column '''
        col = self._sanitizecol(col)
        coldata = self.data[:,col] # Get data for this column
        if key is None: key = coldata[-1] # If not supplied, pick the last element
        try:    index = coldata.tolist().index(key) # Try to find duplicates
        except: 
            if die: raise Exception('Item %s not found; choices are: %s' % (key, coldata))
            else:   return None
        return index
        
    def rmrow(self, key=None, col=None, returnval=False, die=True):
        ''' Like pop, but removes by matching the first column instead of the index -- WARNING, messy '''
        index = self._rowindex(key=key, col=col, die=die)
        if index is not None: self.pop(index)
        return None
    
    def _diffindices(self, indices=None):
        ''' For a given set of indices, get the inverse, in set-speak '''
        if indices is None: indices = []
        ind_set = set(np.array(indices))
        all_set = set(np.arange(self.nrows))
        diff_set = np.array(list(all_set - ind_set))
        return diff_set
    
    def rmrows(self, indices=None):
        ''' Remove rows by index -- WARNING, messy '''
        keep_set = self._diffindices(indices)
        self.data = self.data[keep_set,:]
        return None
    
    def replace(self, col=None, old=None, new=None):
        ''' Replace all of one value in a column with a new value '''
        col = self._sanitizecol(col)
        coldata = self.data[:,col] # Get data for this column
        inds = mh.findinds(coldata==old)
        self.data[inds,col] = new
        return None
        
    
    def _todict(self, row):
        ''' Return row as a dict rather than as an array '''
        if len(row)!=len(self.cols): 
            errormsg = 'Length mismatch between "%s" and "%s"' % (row, self.cols)
            raise Exception(errormsg)
        rowdict = odict(zip(self.cols, row))
        return rowdict
    
    def findrow(self, key=None, col=None, default=None, closest=False, die=False, asdict=False):
        '''
        Return a row by searching for a matching value.
        
        Arguments:
            key = the value to look for
            col = the column to look for this value in
            default = the value to return if key is not found (overrides die)
            closest = whether or not to return the closest row (overrides default and die)
            die = whether to raise an exception if the value is not found
            asdict = whether to return results as dict rather than list
        
        Example:
            df = dataframe(cols=['year','val'],data=[[2016,0.3],[2017,0.5]])
            df.findrow(2016) # returns array([2016, 0.3], dtype=object)
            df.findrow(2013) # returns None, or exception if die is True
            df.findrow(2013, closest=True) # returns array([2016, 0.3], dtype=object)
            df.findrow(2016, asdict=True) # returns {'year':2016, 'val':0.3}
        '''
        if not closest: # Usual case, get 
            index = self._rowindex(key=key, col=col, die=(die and default is None))
        else:
            col = self._sanitizecol(col)
            coldata = self.data[:,col] # Get data for this column
            index = np.argmin(abs(coldata-key)) # Find the closest match to the key
        if index is not None:
            thisrow = self.data[index,:]
            if asdict:
                thisrow = self._todict(thisrow)
        else:
            thisrow = default # If not found, return as default
        return thisrow
    
    
    def findrows(self, key=None, col=None, asarray=False):
        indices = self.rowindex(key=key, col=col)
        arr = self.get(rows=indices)
        if asarray:
            return arr
        else:
            df = dataframe(cols=self.cols, data=arr)
            return df

    
    def rowindex(self, key=None, col=None):
        ''' Return the indices of all rows matching the given key in a given column. '''
        col = self._sanitizecol(col)
        coldata = self.data[:,col] # Get data for this column
        indices = mh.findinds(coldata==key)
        return indices
        
    def _filterrows(self, key=None, col=None, keep=True, verbose=False):
        ''' Filter rows and either keep the ones matching, or discard them '''
        indices = self.rowindex(key=key, col=col)
        if keep: indices = self._diffindices(indices)
        self.rmrows(indices=indices)
        if verbose: print('Dataframe filtering: %s rows removed based on key="%s", column="%s"' % (len(indices), key, col))
        return None
    
    def filter_in(self, key=None, col=None, verbose=False):
        self._filterrows(key=key, col=col, keep=True, verbose=verbose)
        return None
    
    def filter_out(self, key=None, col=None, verbose=False):
        self._filterrows(key=key, col=col, keep=False, verbose=verbose)
        return None
    
    def filtercols(self, cols=None, die=True):
        if cols is None: cols = ut.dcp(self.cols) # By default, do nothing
        cols = ut.promotetolist(cols)
        order = []
        notfound = []
        for col in cols:
            if col in self.cols:
                order.append(self.cols.index(col))
            else:
                cols.remove(col)
                notfound.append(col)
        if len(notfound):
            errormsg = 'Dataframe: could not find the following column(s): %s\nChoices are: %s' % (notfound, self.cols)
            if die: raise Exception(errormsg)
            else:   print(errormsg)
        self.cols = cols # These should be in the correct order
        self.data = self.data[:,order] # Resort and filter the data
        return None
        
    def insert(self, row=0, value=None):
        ''' Insert a row at the specified location '''
        rowindex = int(row)
        value = self._val2row(value) # Make sure it's in the correct format
        self.data = np.vstack((self.data[:rowindex,:], value, self.data[rowindex:,:]))
        return None
    
    def sort(self, col=None, reverse=False):
        ''' Sort the data frame by the specified column '''
        col = self._sanitizecol(col)
        sortorder = np.argsort(self.data[:,col])
        if reverse: sortorder = np.array(list(reversed(sortorder)))
        self.data = self.data[sortorder,:]
        return sortorder
    
    def sortcols(self, reverse=False):
        sortorder = np.argsort(self.cols)
        if reverse: sortorder = np.array(list(reversed(sortorder)))
        self.cols = list(np.array(self.cols)[sortorder])
        self.data = self.data[:,sortorder]
        return sortorder
        
    def jsonify(self, cols=None, rows=None, header=None, die=True):
        ''' Export the dataframe to a JSON-compatible format '''
        
        # Handle input arguments
        if cols   is None: cols   = self.cols # Use all columns by default
        if rows   is None: rows   = list(range(self.nrows)) # Use all rows by default
        if header is None: header = True # Include headers
        
        # Optionally filter columns after making a copy
        exportdf = ut.dcp(self)
        exportdf.filtercols(cols)
        
        # Handle output
        output = []
        if header: output.append(exportdf.cols)
        for r in rows:
            thisrow = []
            for col in exportdf.cols:
                try:
                    datum = exportdf.get(cols=col,rows=r)
                    thisrow.append(datum)
                except:
                    pass # This has already been handled by the validation above
            output.append(thisrow)
        return output
    
    def pandas(self, df=None):
        ''' Function to export to pandas (if no argument) or import from pandas (with an argument) '''
        import pandas as pd # Optional import
        if df is None: # Convert
            output = pd.DataFrame(data=self.data, columns=self.cols)
            return output
        else:
            if type(df) != pd.DataFrame:
                errormsg = 'Can only read pandas dataframes, not %s' % type(df)
                raise Exception(errormsg)
            self.cols = list(df.columns)
            self.data = np.array(df, dtype=object)
            return None
    
    def export(self, filename=None, cols=None, close=True):
        from . import sc_fileio as io # Optional import
        exportdf = ut.dcp(self)
        exportdf.filtercols(cols)
        exportdata = np.vstack((exportdf.cols, exportdf.data))
        filepath = io.savespreadsheet(filename=filename, data=exportdata, close=close)
        return filepath