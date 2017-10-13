extern crate libc;

use self::libc::{c_int, size_t};
use std::io::{Result, Error};
use std::collections::BTreeMap;
use std::ptr;

#[allow(non_camel_case_types)]
pub enum sd_journal {}

macro_rules! ffi_try {
    ($e: expr) => ({
        try!(ffi_to_result(unsafe { $e }))
    })
}

#[link(name = "systemd-journal")]
extern {
    fn sd_journal_open(ret: *mut *mut sd_journal, flags: c_int) -> c_int;
    fn sd_journal_seek_head(j: *mut sd_journal) -> c_int;
    fn sd_journal_seek_realtime_usec(j: *mut sd_journal, usec: u64) -> c_int;

    fn sd_journal_restart_data(j: *mut sd_journal) -> ();
    fn sd_journal_next(j: *mut sd_journal) -> c_int;
    fn sd_journal_get_realtime_usec(j: *mut sd_journal, ret: *const u64) -> c_int;
    fn sd_journal_enumerate_data(j: *mut sd_journal, data: *const *mut u8, l: *mut size_t) -> c_int;

    pub fn sd_journal_close(j: *mut sd_journal) -> ();
}

pub struct Journal {
    j: *mut sd_journal,
}

impl Journal {
    pub fn open() -> Result<Journal> {
        let mut journal = Journal { j: ptr::null_mut() };
        ffi_try!(sd_journal_open(&mut journal.j, 0));
        Ok(journal)
    }

    pub fn seek_head(&mut self) -> Result<()> {
        ffi_try!(sd_journal_seek_head(self.j));
        Ok(())
    }

    pub fn seek(&mut self, usec: u64) -> Result<()> {
        ffi_try!(sd_journal_seek_realtime_usec(self.j, usec));
        Ok(())
    }

    pub fn next(&mut self) -> Result<Option<(u64, BTreeMap<String, String>)>> {
        if ffi_try!(sd_journal_next(self.j)) == 0 {
            return Ok(None);
        }

        unsafe { sd_journal_restart_data(self.j) };

        let mut ret = BTreeMap::new();

        let mut size: size_t = 0;
        let data: *mut u8 = ptr::null_mut();
        while ffi_try!(sd_journal_enumerate_data(self.j, &data, &mut size)) > 0 {
            unsafe {
                let b = ::std::slice::from_raw_parts_mut(data, size);
                let field = ::std::str::from_utf8_unchecked(b);
                let mut name_value = field.splitn(2, '=');
                let name = name_value.next().unwrap();
                let value = name_value.next().unwrap();
                ret.insert(From::from(name), From::from(value));
            }
        }

        let usec = try!(self.realtime_usec());
        Ok(Some((usec, ret)))
    }

    fn realtime_usec(&mut self) -> Result<u64> {
        let mut usec: u64 = 0;
        ffi_try!(sd_journal_get_realtime_usec(self.j, &mut usec));
        Ok(usec)
    }
}

impl Drop for Journal {
    fn drop(&mut self) {
        if !self.j.is_null() {
            unsafe { sd_journal_close(self.j) }
        }
    }
}

fn ffi_to_result(ret: c_int) -> Result<c_int> {
    if ret < 0 {
        Err(Error::from_raw_os_error(-ret))
    } else {
        Ok(ret)
    }
}
