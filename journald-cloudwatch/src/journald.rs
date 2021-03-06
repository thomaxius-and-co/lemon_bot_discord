extern crate libc;

use self::libc::{c_int, c_void, size_t};
use std::io::{Result, Error};
use std::collections::BTreeMap;
use std::ptr;
use std::time::Duration;

pub const SD_JOURNAL_LOCAL_ONLY: c_int = 1;

#[allow(non_camel_case_types)]
pub enum sd_journal {}

macro_rules! ffi_try {
    ($e: expr) => ({
        try!(ffi_to_result(unsafe { $e }))
    })
}

#[link(name = "systemd")]
extern {
    fn sd_journal_open(ret: *mut *mut sd_journal, flags: c_int) -> c_int;
    fn sd_journal_seek_head(j: *mut sd_journal) -> c_int;
    fn sd_journal_seek_realtime_usec(j: *mut sd_journal, usec: u64) -> c_int;

    fn sd_journal_restart_data(j: *mut sd_journal) -> ();
    fn sd_journal_next(j: *mut sd_journal) -> c_int;
    fn sd_journal_previous(j: *mut sd_journal) -> c_int;
    fn sd_journal_get_realtime_usec(j: *mut sd_journal, ret: *const u64) -> c_int;
    fn sd_journal_enumerate_data(j: *mut sd_journal, data: *const *mut u8, l: *mut size_t) -> c_int;

    fn sd_journal_add_match(j: *mut sd_journal, data: *const c_void, size: size_t) -> c_int;

    fn sd_journal_wait(j: *mut sd_journal, timeout_usec: u64) -> c_int;

    pub fn sd_journal_close(j: *mut sd_journal) -> ();
}

pub struct Journal {
    j: *mut sd_journal,
}

impl Journal {
    pub fn open() -> Result<Journal> {
        let mut journal = Journal { j: ptr::null_mut() };
        ffi_try!(sd_journal_open(&mut journal.j, SD_JOURNAL_LOCAL_ONLY));
        Ok(journal)
    }

    pub fn add_match(&mut self, key: &str, val: &str) -> Result<()> {
        let mut filter = Vec::<u8>::from(key);
        filter.push('=' as u8);
        filter.extend(Vec::<u8>::from(val));
        let data = filter.as_ptr() as *const c_void;
        let size = filter.len() as size_t;
        ffi_try!(sd_journal_add_match(self.j, data, size));
        Ok(())
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

        let record = try!(self.get_record());
        Ok(Some(record))
    }

    pub fn previous(&mut self) -> Result<Option<(u64, BTreeMap<String, String>)>> {
        if ffi_try!(sd_journal_previous(self.j)) == 0 {
            return Ok(None);
        }

        let record = try!(self.get_record());
        Ok(Some(record))
    }

    pub fn wait(&mut self, timeout: Option<Duration>) -> Result<()> {
        let timeout_usec = timeout.map(duration_to_usec).unwrap_or(-1i64 as u64);
        // TODO: Return event type when needed
        ffi_try!(sd_journal_wait(self.j, timeout_usec));
        Ok(())
    }

    fn get_record(&mut self) -> Result<(u64, BTreeMap<String, String>)> {
        unsafe { sd_journal_restart_data(self.j) };

        let mut ret = BTreeMap::new();

        let mut size: size_t = 0;
        let data: *mut u8 = ptr::null_mut();
        while ffi_try!(sd_journal_enumerate_data(self.j, &data, &mut size)) > 0 {
            unsafe {
                let b = ::std::slice::from_raw_parts_mut(data, size);
                if let Ok(field) = ::std::str::from_utf8(b) {
                    let mut name_value = field.splitn(2, '=');
                    let name = name_value.next().unwrap();
                    let value = name_value.next().unwrap();
                    ret.insert(From::from(name), From::from(value));
                } else {
                    println!("ERROR journald entry contained field with invalid UTF-8");
                }
            }
        }

        let usec = try!(self.realtime_usec());
        Ok((usec, ret))
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

fn duration_to_usec(d: Duration) -> u64 {
    d.as_secs() * 1_000_000 + (d.subsec_nanos() * 1_000) as u64
}
